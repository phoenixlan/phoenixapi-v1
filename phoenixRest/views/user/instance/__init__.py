from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPNotFound,
    HTTPBadRequest
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow

from phoenixRest.models.core.user import Gender, User
from phoenixRest.models.core.friendship import Friendship
from phoenixRest.models.core.event import Event, get_current_event
from phoenixRest.models.core.avatar import Avatar
from phoenixRest.models.crew.application import Application
from phoenixRest.models.tickets.ticket import Ticket
from phoenixRest.models.tickets.ticket_type import TicketType
from phoenixRest.models.tickets.ticket_voucher import TicketVoucher
from phoenixRest.models.tickets.payment import Payment

from phoenixRest.models.tickets.store_session import StoreSession
from phoenixRest.models.tickets.ticket_transfer import TicketTransfer

from phoenixRest.models.utils.discord_mapping_oauth_state import DiscordMappingOauthState
from phoenixRest.models.utils.discord_mapping import DiscordMapping

from phoenixRest.mappers.user import map_user_with_secret_fields, map_user_public_with_positions
from phoenixRest.mappers.ticket import map_ticket_simple

from phoenixRest.features.crew_card import generate_badge

from phoenixRest.utils import validate, validateUuidAndQuery
from phoenixRest.resource import resource

from phoenixRest.features.discord import DISCORD_OAUTH_REDIRECT_URI, DISCORD_CLIENT_ID, DISCORD_ENABLED, DISCORD_SCOPES

from phoenixRest.roles import HR_ADMIN, ADMIN, TICKET_ADMIN, TICKET_CHECKIN, CREW_CARD_PRINTER, CHIEF

import re

from sqlalchemy import and_, or_, extract

from datetime import datetime, timedelta, date

import urllib
import os

from PIL import Image, ImageOps

import logging
log = logging.getLogger(__name__)


class UserInstanceResource(object):
    def __acl__(self):
        acl = [
            # Who has access to view a user?
            (Allow, HR_ADMIN, 'user_view'),
            (Allow, ADMIN, 'user_view'),
            (Allow, TICKET_ADMIN, 'user_view'),
            (Allow, TICKET_CHECKIN, 'user_view'),
            # Who has access to modify a user?
            (Allow, HR_ADMIN, 'user_modify'),
            (Allow, ADMIN, 'user_modify'),
            # Who has acces to user friendship status?
            (Allow, HR_ADMIN, 'get_friendship_states'),
            (Allow, ADMIN, 'get_friendship_states'),
            # Who can see if an user is a member or not?
            (Allow, HR_ADMIN, 'get_membership_state'),
            (Allow, ADMIN, 'get_membership_state'),
            # Who can view an users store session
            (Allow, ADMIN, 'user_get_store_session'),
            (Allow, TICKET_ADMIN, 'user_get_store_session'),
            # Who can list an users tickets
            (Allow, ADMIN, 'user_list_owned_tickets'),
            (Allow, TICKET_ADMIN, 'user_list_owned_tickets'),
            # Purchased tickets may contain tickets sent to others, so users cannot list them
            (Allow, ADMIN, 'user_list_purchased_tickets'),
            (Allow, TICKET_ADMIN, 'user_list_purchased_tickets'),
            # Seatable tickets are either owned by the user or "lended" to them by another for the sake of seating
            (Allow, ADMIN, 'user_list_seatable_tickets'),
            (Allow, TICKET_ADMIN, 'user_list_seatable_tickets'),
            # Who can list ticket vouchers
            (Allow, ADMIN, 'user_list_ticket_vouchers'),
            (Allow, TICKET_ADMIN, 'user_list_ticket_vouchers'),
            # Ticket transfers
            (Allow, ADMIN, 'user_list_ticket_transfers'),
            (Allow, TICKET_ADMIN, 'user_list_ticket_transfers'),
            # Who can view payments?
            (Allow, ADMIN, 'list_payments'),
            (Allow, TICKET_ADMIN, 'list_payments'),

            # Applications?
            (Allow, ADMIN, 'get_applications'),
            (Allow, CHIEF, 'get_applications'),

            # Who can see discord user mappings?
            (Allow, HR_ADMIN, 'get_discord_mapping'),
            (Allow, ADMIN, 'get_discord_mapping'),

            # Who can remove a Discord mapping?
            (Allow, HR_ADMIN, 'delete_discord_mapping'),
            (Allow, ADMIN, 'delete_discord_mapping'),

            # Who can activate users on others behalf
            (Allow, HR_ADMIN, 'activate_user'),
            (Allow, ADMIN, 'activate_user'),
            
            # Who can view if an user is activated and activate their user?
            (Allow, ADMIN, 'get_activation_state'),

            # Who can view someone's crew card?
            (Allow, ADMIN, 'get_crew_card'),
            (Allow, HR_ADMIN, 'get_crew_card'),
            (Allow, CREW_CARD_PRINTER, 'get_crew_card')
        ]
        if self.request.user is not None:
            acl = acl + [
                # Users can view themselves, always
                (Allow, "%s" % self.userInstance.uuid, 'user_view'),
                (Allow, "%s" % self.userInstance.uuid, 'get_membership_state'),
                # Users can view their friendships and friend_requests
                (Allow, "%s" % self.userInstance.uuid, 'get_friendship_states'),
                # Users can fetch their own tickets
                (Allow, "%s" % self.userInstance.uuid, 'user_list_owned_tickets'),
                (Allow, "%s" % self.userInstance.uuid, 'user_list_purchased_tickets'),
                (Allow, "%s" % self.userInstance.uuid, 'user_list_seatable_tickets'),
                # Users can see their own ticket transfers
                (Allow, "%s" % self.userInstance.uuid, 'user_list_ticket_transfers'),
                (Allow, "%s" % self.userInstance.uuid, 'user_list_ticket_vouchers'),
                # Users can view their own store session
                (Allow, "%s" % self.userInstance.uuid, 'user_get_store_session'),
                # Users can upload their own avatar
                (Allow, "%s" % self.userInstance.uuid, 'avatar_upload'),
                # Users can view their own payments
                (Allow, "%s" % self.userInstance.uuid, 'list_payments'),
                # Users can see their own discord mappings
                (Allow, "%s" % self.userInstance.uuid, 'get_discord_mapping'),
                # Users can create their own discord mappings
                (Allow, "%s" % self.userInstance.uuid, 'create_discord_mapping'),
                # Users can delete their own discord mappings
                (Allow, "%s" % self.userInstance.uuid, 'delete_discord_mapping'),
                # Users can get their own applications
                (Allow, "%s" % self.userInstance.uuid, 'get_applications')
            ]
        return acl

    def __init__(self, request, uuid):
        self.request = request
        log.info("uuid: %s" % uuid)
        self.userInstance = validateUuidAndQuery(request, User, User.uuid, uuid)

        if self.userInstance is None:
            raise HTTPNotFound("User not found")

@view_config(context=UserInstanceResource, name='', request_method='GET', renderer='json', permission='user_view')
def get_user(context, request):
    if TICKET_CHECKIN in request.effective_principals or \
        ADMIN in request.effective_principals or \
        HR_ADMIN in request.effective_principals or \
        request.user.uuid == context.userInstance.uuid:

        log.warning("Sending more details about a user because the query person is an admin or owns the account")
        return map_user_with_secret_fields(context.userInstance, request)
    return map_user_public_with_positions(context.userInstance, request)


#https://stackoverflow.com/questions/201323/how-can-i-validate-an-email-address-using-a-regular-expression
email_regex = re.compile("(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*)@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])")

@view_config(context=UserInstanceResource, name='', request_method='PATCH', renderer='json', permission='user_modify')
def modify_user(context, request):

    # Create an error list
    error = list()

    # Create and check variables
    user_uuid = request.json_body['uuid']

    firstname = None
    if 'firstname' in request.json_body:
        firstname = request.json_body['firstname']
        if type(firstname) != str:
            error.append("invalid type for firstname (not string)")
        if len(firstname) < 1:
            error.append("firstname cannot be empty")

    lastname = None
    if 'lastname' in request.json_body:
        lastname = request.json_body['lastname']
        if type(lastname) != str:
            error.append("invalid type for lastname (not string)")
        if len(lastname) < 1:
            error.append("lastname cannot be empty")

    username = None
    if 'username' in request.json_body:
        username = request.json_body['username']
        if type(username) != str:
            error.append("invalid type for username (not string)")
        if len(username) < 1:
            error.append("username cannot be empty")
        if request.db.query(User).filter(and_( 
                User.username == username, 
                User.uuid != user_uuid
            )).first():
            error.append("username is already in use")
  
    email = None
    if 'email' in request.json_body:
        email = request.json_body['email']
        if type(email) != str:
            error.append("invalid type for email (not string)")
        if email_regex.match(email) is None:
            error.append("invalid email formatting - regex match failure") 
        if request.db.query(User).filter(and_(
                User.email == email.lower(), 
                User.uuid != user_uuid
            )).first():
            error.append("email is already in use")

    phone = None
    if 'phone' in request.json_body:
        phone = request.json_body['phone']
        if type(phone) != str:
            error.append("invalid type for phone (not string)")
        if len(phone) < 1:
            error.append("phone cannot be empty")
        if request.db.query(User).filter(and_(
                User.phone == phone, 
                User.uuid != user_uuid
            )).first():
            error.append("phone number is already in use")

    guardian_phone = None
    if 'guardian_phone' in request.json_body:
        guardian_phone = request.json_body['guardian_phone']
        if type(guardian_phone) != str:
            error.append("invalid type for guardian_phone (not string)")

    address = None
    if 'address' in request.json_body:
        address = request.json_body['address']
        if type(address) != str:
            error.append("invalid type for address (not string)")
        if len(address) < 1:
            error.append("address cannot be empty")

    postal_code = None
    if 'postal_code' in request.json_body:
        postal_code = request.json_body['postal_code']
        if type(postal_code) != str:
            error.append("invalid type for postal_code (not string)")
        if len(postal_code) < 1:
            error.append("postal code cannot be empty")
  
    birthdate = None
    if 'birthdate' in request.json_body:
        local_birthdate = request.json_body['birthdate']
        if type(local_birthdate) != str:
            error.append("invalid type for local_birthdate (not string)")
        if len(local_birthdate) < 1:
            error.append("local-birthdate cannot be empty")
            print(local_birthdate)
        else:
            try:
                birthdate = date.fromisoformat(local_birthdate)
            except:
                error.append("failed to format birthdate to isoformat - invalid input.")

            if birthdate:
                if birthdate > date.today():
                    error.append("invalid birthdate - cannot be in future")

    gender = None
    if 'gender' in request.json_body:
        local_gender = request.json_body['gender']
        if type(local_gender) != str:
            error.append("invalid type for local_gender (not string)")
        if(local_gender == "male"):
            gender = Gender.male
        elif(local_gender == "female"):
            gender = Gender.female
        else:
            error.append("invalid gender (not male or female)")

    # Check if any errors occured while checking the variables and return them
    if len(error) > 0:
        request.response.status = 400
        return {
            'error': "An error occured when attempting to update user information: %s." % ", ".join(error)
        }
        
    # All checks passed, set the variables to the database and return a success message!
    if firstname is not None: context.userInstance.firstname = firstname
    if lastname is not None: context.userInstance.lastname = lastname
    if username is not None: context.userInstance.username = username
    if email is not None: context.userInstance.email = email
    if phone is not None: context.userInstance.phone = phone
    if guardian_phone is not None: context.userInstance.guardian_phone = guardian_phone
    if address is not None: context.userInstance.address = address
    if postal_code is not None: context.userInstance.postal_code = postal_code
    if birthdate is not None: context.userInstance.birthdate = birthdate
    if gender is not None: context.userInstance.gender = gender
    
    return {
        'info': 'User information updated successfully!',
    }


@view_config(context=UserInstanceResource, name='friendships', request_method='GET', renderer='json', permission='get_friendship_states')
def get_friendships(context, request):
    query = request.db.query(Friendship).filter(
        or_(
            Friendship.source_user == context.userInstance, # Source
            and_(
                Friendship.recipient_user == context.userInstance, # Recipient
                Friendship.revoked == None
            )
        )
    ).all()
    return query

@view_config(context=UserInstanceResource, name='owned_tickets', request_method='GET', renderer='json', permission='user_list_owned_tickets')
def get_owned_tickets(context, request):
    query = request.db.query(Ticket)
    if 'event' in request.GET:
        event = request.db.query(Event).filter(Event.uuid == request.get['event']).first()
        if event is None:
            request.response.status = 404
            return {
                'error': 'Event not found'
            }
        query = query.filter(and_(Ticket.owner == context.userInstance, Ticket.event == event))
    else:
        query = query.filter(Ticket.owner == context.userInstance)
    return query.all()

@view_config(context=UserInstanceResource, name='ticket_vouchers', request_method='GET', renderer='json', permission='user_list_ticket_vouchers')
def get_ticket_vouchers(context, request):
    return request.db.query(TicketVoucher).filter(TicketVoucher.recipient_user == context.userInstance).all()

# We only care about transfers from this event
@view_config(context=UserInstanceResource, name='ticket_transfers', request_method='GET', renderer='json', permission='user_list_ticket_transfers')
def get_ticket_transfers(context, request):
    event = None
    if 'event_uuid' in request.GET:
        event = request.db.query(Event).filter(Event.uuid == request.GET['event_uuid']).first()
        if event is None:
            request.response.status = 404
            return {
                'error': "Event not found"
            }
    else:
        event = get_current_event(request)

    transfers = request.db.query(TicketTransfer).filter(and_(TicketTransfer.ticket.has(Ticket.event_uuid == event.uuid), or_(
        or_(TicketTransfer.from_user == context.userInstance),
        or_(TicketTransfer.to_user == context.userInstance)
    ))).all()
    return transfers

@view_config(context=UserInstanceResource, name='purchased_tickets', request_method='GET', renderer='json', permission='user_list_purchased_tickets')
def get_purchased_tickets(context, request):
    query = request.db.query(Ticket)
    if 'event' in request.GET:
        event = request.db.query(Event).filter(Event.uuid == request.get['event']).first()
        if event is None:
            request.response.status = 404
            return {
                'error': 'Event not found'
            }
        query = query.filter(and_(Ticket.buyer == context.userInstance, Ticket.event == event))
    else:
        query = query.filter(Ticket.buyer == context.userInstance)
    return query.all()

@view_config(context=UserInstanceResource, name='seatable_tickets', request_method='GET', renderer='json', permission='user_list_seatable_tickets')
def get_seatable_tickets(context, request):
    query = request.db.query(Ticket)
    if 'event_uuid' in request.GET:
        event = request.db.query(Event).filter(Event.uuid == request.GET['event_uuid']).first()
        if event is None:
            request.response.status = 404
            return {
                'error': 'Event not found'
            }
        query = query.join(TicketType, Ticket.ticket_type_uuid == TicketType.uuid).filter(and_(
            TicketType.seatable == True,
            Ticket.event == event,
            or_(
                Ticket.seater== context.userInstance,
                and_(Ticket.seater == None, Ticket.owner == context.userInstance)
            )
        ))
    else:
        query = query.join(TicketType, Ticket.ticket_type_uuid == TicketType.uuid).filter(and_(
            TicketType.seatable == True,
            or_(
                Ticket.seater == context.userInstance, 
                and_(Ticket.seater == None, Ticket.owner == context.userInstance)
            )
        ))
    return query.all()

@view_config(context=UserInstanceResource, name='payments', request_method='GET', renderer='json', permission='list_payments')
def get_payments(context, request):
    payments = request.db.query(Payment).filter(Payment.user == context.userInstance).all()
    return payments

@view_config(context=UserInstanceResource, name='store_session', request_method='GET', renderer='json', permission='user_get_store_session')
def get_store_session(context, request):
    session_lifetime = int(request.registry.settings["ticket.store_session_lifetime"])

    too_old = datetime.now() - timedelta(seconds=session_lifetime)

    session = request.db.query(StoreSession).filter(or_(StoreSession.user == context.userInstance, StoreSession.created < too_old)).first()
    if session is not None:
        return session
    raise HTTPNotFound("User does not have an active store session")

@view_config(context=UserInstanceResource, name='activation', request_method='GET', renderer='json', permission='get_activation_state')
def get_activation_state(context, request):
    return {
        "activated" :context.userInstance.activation_code is None
    }

@view_config(context=UserInstanceResource, name='activation', request_method='PATCH', renderer='json', permission='activate_user')
def activate_user(context, request):
    if context.userInstance.activation_code is None:
        request.response.status = 400
        return {
            "error": "User is already activated"
        }
    
    request.db.delete(context.userInstance.activation_code)
    return {
        'info': 'User activated successfully!'
    }

@view_config(context=UserInstanceResource, name='avatar', request_method='POST', renderer='json', permission='avatar_upload')
@validate(post={'x': str, 'y': str, 'w': str, 'h': str})
def upload_avatar(context, request):
    if context.userInstance.avatar is not None:
        raise HTTPBadRequest("You already have an avatar, delete that first")
    log.info("%s" % request.POST)
    if "file" not in request.POST:
        raise HTTPBadRequest("No file specified")

    filename = request.POST['file'].filename
    log.debug("Got file upload with original name %s" % filename)

    extension = filename.split(".")[-1]

    if extension not in ['jpg', 'jpeg', 'png']:
        raise HTTPBadRequest("Invalid file type")

    _file_handle = request.POST['file'].file

    # Validate the image
    min_w = int(request.registry.settings["avatar.min_w"])
    min_h = int(request.registry.settings["avatar.min_h"])

    _file_handle.seek(0)
    im = Image.open(_file_handle)
    im = ImageOps.exif_transpose(im)
  
    # Size of the image in pixels (size of orginal image)
    # (This is not mandatory)
    orig_width, orig_height = im.size
    if orig_width < min_w or orig_height < min_h:
        raise HTTPBadRequest("Image is too small")

    # Validate cropping
    x = int(request.POST['x'])
    y = int(request.POST['y'])

    w = int(request.POST['w'])
    h = int(request.POST['h'])

    if x + w > orig_width:
        raise HTTPBadRequest('Cropping box is outside the image(width)')

    if y + h > orig_height:
        raise HTTPBadRequest('Cropping box is outside the image(height)')

    if x < 0 or y < 0:
        raise HTTPBadRequest('Cropping box is outside the image(x or y is negative wtf)')

    if w < min_w or h < min_h:
        raise HTTPBadRequest('Cropping box is too small')

    # Create an avatar so we can copy the file to the correct file name
    avatar = Avatar(context.userInstance, "jpg")
    request.db.add(avatar)
    request.db.flush()
    log.info("Created new avatar %s" % avatar.uuid)

    # Crop the image
    im = im.crop((x, y, x+w, y+h))
    
    # Deal with transparency
    if im.mode != "RGB":
        background = Image.new('RGBA', im.size, (255,255,255))

        # Alpha composite function only accepts RGBA
        if im.mode != "RGBA":
            im = im.convert("RGBA")

        im = Image.alpha_composite(background, im)
        im = im.convert("RGB")


    # Make sure the directories we need exist
    avatar_thumb_dir = request.registry.settings["avatar.directory_thumb"]
    avatar_sd_dir = request.registry.settings["avatar.directory_sd"]
    avatar_hd_dir = request.registry.settings["avatar.directory_hd"]

    # Ensure paths are created
    if not os.path.exists(avatar_thumb_dir):
        os.makedirs(avatar_thumb_dir)
    if not os.path.exists(avatar_sd_dir):
        os.makedirs(avatar_sd_dir)
    if not os.path.exists(avatar_hd_dir):
        os.makedirs(avatar_hd_dir)


    avatar_thumb_path = os.path.join(avatar_thumb_dir, "%s.jpg" % avatar.uuid)
    avatar_sd_path = os.path.join(avatar_sd_dir, "%s.jpg" % avatar.uuid)
    avatar_hd_path = os.path.join(avatar_hd_dir, "%s.jpg" % avatar.uuid)
    
    # Fetch avatar sizes from settings
    avatar_thumb_w = int(request.registry.settings["avatar.thumb_w"])
    avatar_thumb_h = int(request.registry.settings["avatar.thumb_h"])

    avatar_sd_w = int(request.registry.settings["avatar.sd_w"])
    avatar_sd_h = int(request.registry.settings["avatar.sd_h"])

    avatar_hd_w = int(request.registry.settings["avatar.hd_w"])
    avatar_hd_h = int(request.registry.settings["avatar.hd_h"])

    im.resize((avatar_thumb_w,avatar_thumb_h), Image.LANCZOS).save(avatar_thumb_path, "JPEG", quality=80)
    im.resize((avatar_sd_w,avatar_sd_h), Image.LANCZOS).save(avatar_sd_path, "JPEG", quality=100)
    im.resize((avatar_hd_w,avatar_hd_h), Image.LANCZOS).save(avatar_hd_path, "JPEG", quality=100)


    return avatar

@view_config(context=UserInstanceResource, name='membership', request_method='GET', renderer='json', permission='get_membership_state')
def get_membership_information(context, request):
    year = datetime.now().year
    if "year" in request.GET:
        year = int(request.GET['year'])

    member_granting_tickets = request.db.query(Ticket).join(TicketType, Ticket.ticket_type_uuid==TicketType.uuid).join(Event, Ticket.event_uuid == Event.uuid) \
        .filter(and_(extract('year', Event.start_time) == year, TicketType.grants_membership == True, Ticket.owner_uuid == context.userInstance.uuid)).all()
    
    return {
        'is_member': len(member_granting_tickets) > 0
    }

@view_config(context=UserInstanceResource, name='discord_mapping', request_method='GET', renderer='json', permission='get_discord_mapping')
def get_discord_mapping(context, request):
    if context.userInstance.discord_mapping is None:
        request.response.status = 404
        return {
            "error": "No discord mapping"
        }
    return context.userInstance.discord_mapping

@view_config(context=UserInstanceResource, name='discord_mapping', request_method='DELETE', renderer='json', permission='delete_discord_mapping')
def remove_discord_mapping(context, request):
    if context.userInstance.discord_mapping is None:
        request.response.status = 404
        return {
            "error": "No discord mapping"
        }
    
    request.service_manager.get_service('email').send_mail(context.userInstance.email, "Tilkobling til Discord-konto er fjernet", "discord_oauth_removed.jinja2", {
        "mail": request.registry.settings["api.contact"],
        "name": request.registry.settings["api.name"]
    })
    
    request.db.delete(context.userInstance.discord_mapping)
    return {}

# Creates the URL which the user needs to visit in order to authenticate with Discord.
@view_config(context=UserInstanceResource, name='discord_mapping', request_method='POST', renderer='json', permission='create_discord_mapping')
def create_discord_mapping_oauth_url(context, request):
    if not DISCORD_ENABLED:
        request.response.status = 400
        log.warn("User tried to initiate Discord mapping flow, but Discord functionality is not enabled on this server")
        return {
            "error": "Discord functionality not enabled on this server"
        }
    # Create a state variable
    discord_mapping_state = DiscordMappingOauthState(context.userInstance)
    request.db.add(discord_mapping_state)

    # Initialize discord oauth variables
    client_id = DISCORD_CLIENT_ID
    state = discord_mapping_state.code
    redirect_uri = urllib.parse.quote_plus(DISCORD_OAUTH_REDIRECT_URI)
    return {
        "url": "https://discord.com/oauth2/authorize?response_type=code&client_id=%s&scope=%s&state=%s&redirect_uri=%s&prompt=consent" % (
            client_id,
            DISCORD_SCOPES,
            state,
            redirect_uri
        )
    }

# Generates a crew card
@view_config(context=UserInstanceResource, name='crew_card', request_method='GET', renderer='pillow', permission='get_crew_card')
def create_crew_card(context, request):
    return generate_badge(request, context.userInstance, get_current_event(request))

@view_config(context=UserInstanceResource, name='applications', request_method='GET', renderer='json', permission='get_applications')
def get_applications(context, request):
    # Find all applications and sort them by time created
    applications = request.db.query(Application) \
        .filter(and_(
            Application.user == context.userInstance,
            Application.hidden == False
        )) \
        .order_by(Application.created.asc()).all()
    return applications
