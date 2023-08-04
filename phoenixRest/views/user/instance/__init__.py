from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPNotFound,
    HTTPBadRequest
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow

from phoenixRest.models.core.user import User
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

from sqlalchemy import and_, or_, extract

from datetime import datetime, timedelta

import urllib
import os

from PIL import Image, ImageOps

import logging
log = logging.getLogger(__name__)


class UserInstanceResource(object):
    def __acl__(self):
        acl = [
            # Who has access to view an user?
            (Allow, HR_ADMIN, 'user_view'),
            (Allow, ADMIN, 'user_view'),
            (Allow, TICKET_ADMIN, 'user_view'),
            (Allow, TICKET_CHECKIN, 'user_view'),
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
                # Users can fetch their own tickets
                (Allow, "%s" % self.userInstance.uuid, 'user_list_owned_tickets'),
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

@view_config(context=UserInstanceResource, name='friendships', request_method='GET', renderer='json', permission='')
def get_friendships(context, request):
    query = request.db.query(Friendship).filter(and_(
        and_(Friendship.accepted is not None, Friendship.revoked is None),
        or_(Friendship.recipient_user == context.userInstance, Friendship.source_user == context.userInstance))
    ).all()
    return query
    
@view_config(context=UserInstanceResource, name='friend_requests', request_method='GET', renderer='json', permission='')
def get_friend_requests(context, request):
    query = request.db.query(Friendship).filter(and_(
        and_(Friendship.accepted is None, Friendship.revoked is not None),
        or_(Friendship.recipient_user == context.userInstance, Friendship.source_user == context.userInstance))
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

@view_config(context=UserInstanceResource, name='activation', request_method='PATCH', renderer='text', permission='activate_user')
def activate_user(context, request):
    if context.userInstance.activation_code is None:
        request.response.status = 400
        return {
            "error": "User is already activated"
        }
    request.db.delete(context.userInstance.activation_code)
    return ""

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

    # Deal with RGBA
    if im.mode in ('RGBA', 'LA') or (im.mode == 'P' and 'transparency' in im.info):
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
    
    request.mail_service.send_mail(context.userInstance.email, "Tilkobling til Discord-konto er fjernet", "discord_oauth_removed.jinja2", {
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