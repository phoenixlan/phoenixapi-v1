from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPNotFound,
    HTTPBadRequest
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow

from phoenixRest.models import db
from phoenixRest.models.core.user import User
from phoenixRest.models.core.event import Event, get_current_event
from phoenixRest.models.core.avatar import Avatar
from phoenixRest.models.tickets.ticket import Ticket
from phoenixRest.models.tickets.ticket_type import TicketType
from phoenixRest.models.tickets.payment import Payment

from phoenixRest.models.tickets.store_session import StoreSession
from phoenixRest.models.tickets.ticket_transfer import TicketTransfer

from phoenixRest.mappers.user import map_user_with_secret_fields, map_user_public_with_positions
from phoenixRest.mappers.ticket import map_ticket_simple

from phoenixRest.utils import validate, validateUuidAndQuery
from phoenixRest.resource import resource

from phoenixRest.roles import HR_ADMIN, ADMIN, TICKET_ADMIN, TICKET_SEATING

from sqlalchemy import and_, or_, extract

from datetime import datetime, timedelta

import shutil
import os

from PIL import Image

import logging
log = logging.getLogger(__name__)


class UserInstanceResource(object):
    def __acl__(self):
        acl = [
            # Who has access to view an user?
            (Allow, HR_ADMIN, 'user_view'),
            (Allow, ADMIN, 'user_view'),
            (Allow, TICKET_ADMIN, 'user_view'),
            (Allow, TICKET_SEATING, 'user_view'),
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
            # Ticket transfers
            (Allow, ADMIN, 'user_list_ticket_transfers'),
            (Allow, TICKET_ADMIN, 'user_list_ticket_transfers'),
            # Who can view payments?
            (Allow, ADMIN, 'list_payments'),
            (Allow, TICKET_ADMIN, 'list_payments'),

            # Who can activate users on others behalf
            (Allow, ADMIN, 'activate_user'),
            # Who can view if an user is activated and activate their user?
            (Allow, ADMIN, 'get_activation_state'),
            # Authenticated pages
            #(Allow, Authenticated, Authenticated),
            #(Deny, Everyone, Authenticated),
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
                # Users can view their own store session
                (Allow, "%s" % self.userInstance.uuid, 'user_get_store_session'),
                # Users can upload their own avatar
                (Allow, "%s" % self.userInstance.uuid, 'avatar_upload'),
                # Users can view their own payments
                (Allow, "%s" % self.userInstance.uuid, 'list_payments'),
            ]
        return acl

    def __init__(self, request, uuid):
        self.request = request
        log.info("uuid: %s" % uuid)
        self.userInstance = validateUuidAndQuery(User, User.uuid, uuid)

        if self.userInstance is None:
            raise HTTPNotFound("User not found")

@view_config(context=UserInstanceResource, name='', request_method='GET', renderer='json', permission='user_view')
def get_user(context, request):
    if ADMIN in request.effective_principals or HR_ADMIN in request.effective_principals or request.user.uuid == context.userInstance.uuid:
        log.warning("Sending more details about a user because the query person is an admin or owns the account")
        return map_user_with_secret_fields(context.userInstance, request)
    return map_user_public_with_positions(context.userInstance, request)


@view_config(context=UserInstanceResource, name='owned_tickets', request_method='GET', renderer='json', permission='user_list_owned_tickets')
def get_owned_tickets(context, request):
    query = db.query(Ticket)
    if 'event' in request.GET:
        event = db.query(Event).filter(Event.uuid == request.get['event']).first()
        if event is None:
            request.response.status = 404
            return {
                'error': 'Event not found'
            }
        query = query.filter(and_(Ticket.owner == context.userInstance, Ticket.event == event))
    else:
        query = query.filter(Ticket.owner == context.userInstance)
    return query.all()

# We only care about transfers from this event
@view_config(context=UserInstanceResource, name='ticket_transfers', request_method='GET', renderer='json', permission='user_list_ticket_transfers')
def get_ticket_transfers(context, request):
    event = None
    if 'event_uuid' in request.GET:
        event = db.query(Event).filter(Event.uuid == request.GET['event_uuid']).first()
        if event is None:
            request.response.status = 404
            return {
                'error': "Event not found"
            }
    else:
        event = get_current_event()

    transfers = db.query(TicketTransfer).filter(and_(TicketTransfer.ticket.has(Ticket.event_uuid == event.uuid), or_(
        or_(TicketTransfer.from_user == context.userInstance),
        or_(TicketTransfer.to_user == context.userInstance)
    ))).all()
    return transfers

@view_config(context=UserInstanceResource, name='purchased_tickets', request_method='GET', renderer='json', permission='user_list_purchased_tickets')
def get_purchased_tickets(context, request):
    query = db.query(Ticket)
    if 'event' in request.GET:
        event = db.query(Event).filter(Event.uuid == request.get['event']).first()
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
    query = db.query(Ticket)
    if 'event' in request.GET:
        event = db.query(Event).filter(Event.uuid == request.get['event']).first()
        if event is None:
            request.response.status = 404
            return {
                'error': 'Event not found'
            }
        query = query.join(TicketType, Ticket.ticket_type_uuid == TicketType.uuid).filter(and_(
            TicketType.seatable == True,
            or_(
                and_(Ticket.seater== context.userInstance, Ticket.event == event), 
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
    payments = db.query(Payment).filter(Payment.user == context.userInstance).all()
    return payments

@view_config(context=UserInstanceResource, name='store_session', request_method='GET', renderer='json', permission='user_get_store_session')
def get_store_session(context, request):
    session_lifetime = int(request.registry.settings["ticket.store_session_lifetime"])

    too_old = datetime.now() - timedelta(seconds=session_lifetime)

    session = db.query(StoreSession).filter(or_(StoreSession.user == context.userInstance, StoreSession.created < too_old)).first()
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
    db.delete(context.userInstance.activation_code)
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

    # Create an avatar so we can copy the file to the correct file name
    avatar = Avatar(context.userInstance, "jpg")
    db.add(avatar)
    db.flush()
    log.info("Created new avatar %s" % avatar.uuid)

    # Validate the image
    min_w = int(request.registry.settings["avatar.min_w"])
    min_h = int(request.registry.settings["avatar.min_h"])

    _file_handle.seek(0)
    im = Image.open(_file_handle)
  
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

    im.resize((avatar_thumb_w,avatar_thumb_h), Image.ANTIALIAS).save(avatar_thumb_path, "JPEG", quality=80)
    im.resize((avatar_sd_w,avatar_sd_h), Image.ANTIALIAS).save(avatar_sd_path, "JPEG", quality=100)
    im.resize((avatar_hd_w,avatar_hd_h), Image.ANTIALIAS).save(avatar_hd_path, "JPEG", quality=100)


    return avatar

@view_config(context=UserInstanceResource, name='membership', request_method='GET', renderer='json', permission='get_membership_state')
def get_membership_information(context, request):
    year = datetime.now().year
    if "year" in request.GET:
        year = int(request.GET['year'])

    member_granting_tickets = db.query(Ticket).join(TicketType, Ticket.ticket_type_uuid==TicketType.uuid).join(Event, Ticket.event_uuid == Event.uuid) \
        .filter(and_(extract('year', Event.start_time) == year, TicketType.grants_membership == True, Ticket.owner_uuid == context.userInstance.uuid)).all()
    
    return {
        'is_member': len(member_granting_tickets) > 0
    }
