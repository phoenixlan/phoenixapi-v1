from pyramid.view import view_config
from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPBadRequest
)

from sqlalchemy import or_, and_

from phoenixRest.models.core.user import User
from phoenixRest.models.crew.position_mapping import PositionMapping
from phoenixRest.models.crew.position import Position
from phoenixRest.models.core.event import get_current_events
from phoenixRest.models.core.oauth.oauthCode import OauthCode
from phoenixRest.models.core.oauth.refreshToken import OauthRefreshToken

from phoenixRest.utils import validate

from datetime import datetime

import logging
log = logging.getLogger(__name__)

def generate_token(user: User, request):
    log.warning("Generating token")
    # We now need to fetch the users permissions
    # https://stackoverflow.com/questions/952914/how-to-make-a-flat-list-out-of-list-of-lists
    # Extract positions that are for current event, or that are lifetime
    current_events = get_current_events(request.db)

    # Position mappings that are currently applicable
    # The key insight here is that we never care about mappings belonging to old events: they are considered read-only
    current_position_mappings = request.db.query(PositionMapping).join(Position).filter(and_(
        PositionMapping.user == user, 
        or_(
            PositionMapping.event == None,
            PositionMapping.event_uuid.in_(current_events)
        )
    )).all()

    # Validate: It is technically possible to create a position binding bound to an event that does not belong to the brand of a position.
    # If this happens, crash and burn instead of giving the user an invalid, possibly exploitable token
    for mapping in current_position_mappings:
        if mapping.event_uuid is not None:
            log.info(f"Checking mapping with event uuid {mapping.event_uuid} and position brand uuid {mapping.position.event_brand_uuid} vs {mapping.event.event_brand_uuid}")
            if mapping.event.event_brand_uuid != mapping.position.event_brand_uuid:
                raise ValueError(f"Position mapping {mapping.uuid} is invalid - bound to event {mapping.event_uuid} of brand {mapping.event.event_brand_uuid} but position belongs to brand {mapping.position.event_brand_uuid}")

    def get_scoped_permissions(position_map):
        """Takes a permission mapping and deduces the proper scoped principals given the position.
        We do this by checking the position we are mapping the user to: 
        A position mapped to a brand is limited, if it isn't its a special global permission"""

        if position_map.position.event_brand_uuid is not None:
            # This position belongs to an event brand
            return [ f"brand:{position_map.position.event_brand_uuid}:{permission.permission}" for permission in position_map.position.permissions ]
        else:
            # This position does not belong to a brand, so we apply it globally
            # TODO: with this system, only permissions that support global scope will work here
            return [ f"global:{permission.permission}" for permission in position_map.position.permissions ]

    # Create a set of all permissions you have
    # A list of list of strings
    permission_map = [ get_scoped_permissions(mapping) for mapping in current_position_mappings] 

    # Flat list of all permissions
    flat_set = set([item for sublist in permission_map for item in sublist])

    # Add permissions caused by positions
    for mapping in current_position_mappings:
        if mapping.position.crew is not None:
            # The user is a crew member for a given brand
            flat_set.add(f"brand:{mapping.position.crew.event_brand_uuid}:member")
            flat_set.add(f"member")
        if mapping.position.chief and mapping.position.crew is not None:
            # The user is chief for a given crew
            flat_set.add(f"chief:{mapping.position.crew.uuid}")
            flat_set.add(f"chief")
            # The user is chief for any crew in a given brand
            flat_set.add(f"brand:{mapping.position.crew.event_brand_uuid}:chief")

    flat_set.add("user:%s" % user.uuid)

    log.info("Permissions: %s" % flat_set)

    return request.create_jwt_token(str(user.uuid), roles=list(flat_set))

@view_config(route_name='login', request_method='POST', renderer='json', permission='auth')
def login(request):
    login = request.json_body['login']
    password = request.json_body['password']
    user = request.db.query(User).filter(User.email == login.lower()).first()

    if user is not None:
        if user.activation_code is not None:
            request.response.status = 403
            return {
                'error': "Kontoen er ikke aktivert - sjekk innboksen din"
            }
        if user.verify_password(password):
            # Create a code that can be exchanged for an oauth token
            code = OauthCode(user)
            request.db.add(code)
            return {
                'code': code.code
            }
        else:
            request.response.status = 403
            return {
                "error": "Invalid email or password"
            }
    else:
        request.response.status = 403
        return {
            "error": "Invalid email or password"
        }
 
@view_config(route_name='oauth_token', request_method='POST', renderer='json')
def token(request):
    # Oauth compliant
    if request.POST['grant_type'] == 'authorization_code':
        # Exchange access code for token
        code = request.db.query(OauthCode).filter(OauthCode.code == request.POST['code']).first()
        if code is None:
            log.info("Not seen before code")

            request.response.status = 403
            return {
                "error": "Invalid code"
            }
        if datetime.now() > code.expires:
            log.warning("Expired code")

            request.response.status = 403
            return {
                "error": "Invalid code"
            }
        user = code.user

        if user is None:
            log.info('User is none when generating token!')
            request.response.status = 500
            return {
                "error": "Failed to get token"
            }

        # The code can only be used once
        request.db.delete(code)
        log.info("Deleted code from database")

        refresh_token = OauthRefreshToken(user, request.headers.get('User-Agent', ""))
        request.db.add(refresh_token)

        token = generate_token(user, request)
        
        # https://www.oauth.com/oauth2-servers/access-tokens/access-token-response/
        return {
            'access_token': token,
            'refresh_token': refresh_token.token,
            'token_type': "Bearer" 
        }
    elif request.POST['grant_type'] == 'refresh_token':
        if 'refresh_token' not in request.POST:
            request.response.status = 400
            return {
                "error": "Missing refresh_token"
            }
        refreshToken = request.db.query(OauthRefreshToken).filter(OauthRefreshToken.token == request.POST['refresh_token']).first()
        if refreshToken is None:
            # TODO rate limit
            request.response.status = 403
            return {
                "error": "Invalid token"
            }
    
        #refreshToken.refresh()
        # The refresh token was valid

        return {
            'access_token': generate_token(refreshToken.user, request),
            #'refresh_token': refreshToken.token
        }
    else:
        request.response.status = 400
        return {
            "error": "Invalid grant type"
        }

# Make sure token returns 200 OK
@view_config(route_name='oauth_token', request_method='OPTIONS', renderer='string')
def token_options(request):
    return ""

@view_config(route_name='oauth_validate', request_method="GET", renderer='string')
def validate_oauth(request):
    if 'client_id' not in request.GET or 'redirect_uri' not in request.GET:
        request.response.status = 400
        return {
            "error": "Missing parameters"
        }
    client_id = request.GET['client_id']
    if client_id not in request.registry.settings["oauth.valid_client_ids"].split(","):
        log.warn("Failed to validate oAuth: %s is an invalid client id" % client_id)
        request.response.status = 400
        return {
            "error": "Invalid client id"
        }
    url = request.registry.settings["oauth.%s.redirect_url" % client_id]
    if url != request.GET['redirect_uri']:
        log.warn("Failed to validate oauth: Invalid URI %s for client id %s" % (request.GET['redirect_uri'], client_id))
        request.response.status = 400
        return {
            "error": "Invalid redirect URI"
        }
    return ""
