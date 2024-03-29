from pyramid.view import view_config
from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPBadRequest
)

from sqlalchemy import or_, and_

from phoenixRest.models.core.user import User
from phoenixRest.models.crew.position_mapping import PositionMapping
from phoenixRest.models.crew.position import Position
from phoenixRest.models.core.event import get_current_event
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
    current_event = get_current_event(request)

    current_positions = request.db.query(Position).join(PositionMapping).filter(and_(
        PositionMapping.user == user, 
        or_(
            PositionMapping.event == None,
            PositionMapping.event == current_event
        )
    )).all()

    position_map = [ position.permissions for position in current_positions ] 

    flat_list = [item for sublist in position_map for item in sublist]

    flat_set = set([entry.permission for entry in flat_list])

    # Add permissions caused by positions
    for position in current_positions:
        if position.crew is not None:
            flat_set.add("member")
        if position.chief and position.crew is not None:
            flat_set.add("chief:%s" % position.crew.uuid)
            # This is only added once since flat_set is a set
            flat_set.add("chief")

    flat_set.add("user:%s" % user.uuid)

    log.debug("Permissions: %s" % flat_set)

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
            log.warning("Created oauth code: %s" % code.code)
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
        log.info("Looking for: %s" % request.POST['code'])

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
