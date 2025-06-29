from operator import and_
from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPNotFound,
    HTTPBadRequest
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow

from phoenixRest.models.core.user import User
from phoenixRest.models.core.event import get_current_event
from phoenixRest.models.tickets.ticket_transfer import TicketTransfer
from phoenixRest.models.tickets.ticket import Ticket
from phoenixRest.models.tickets.seat import Seat

from phoenixRest.roles import ADMIN, TICKET_ADMIN, TICKET_CHECKIN

from phoenixRest.utils import validate 

from sqlalchemy import and_

from datetime import datetime, timedelta

import logging
log = logging.getLogger(__name__)


class TicketInstanceResource(object):
    def __acl__(self):
        acl = [
            (Allow, ADMIN, 'view_ticket'),
            (Allow, TICKET_ADMIN, 'view_ticket'),
            (Allow, TICKET_CHECKIN, 'view_ticket'),
            (Allow, ADMIN, 'seat_ticket'),
            (Allow, TICKET_ADMIN, 'seat_ticket'),
            (Allow, ADMIN, 'set_seater'),
            (Allow, TICKET_ADMIN, 'set_seater'),
            (Allow, ADMIN, 'check_in'),
            (Allow, TICKET_ADMIN, 'check_in'),
            (Allow, TICKET_CHECKIN, 'check_in'),
            (Allow, ADMIN, 'view_ticket_transfer_log'),
            (Allow, TICKET_ADMIN, 'view_ticket_transfer_log'),
        ]
        if self.ticketInstance is not None:
            acl = acl + [
                # Ticket owner can view their own ticket
                (Allow, "%s" % self.ticketInstance.owner.uuid, 'view_ticket'),
                # Ticket owner can transfer their ticket
                (Allow, "%s" % self.ticketInstance.owner.uuid, 'transfer_ticket'),
                # Ticket owner can set the seater of their ticket
                (Allow, "%s" % self.ticketInstance.owner.uuid, 'set_seater'),

                # Ticket owner can seat their own ticket
                (Allow, "%s" % self.ticketInstance.owner.uuid, 'seat_ticket'),
            ]
            if self.ticketInstance.seater is not None:
                # Seaters can also seat the ticket
                acl = acl + [
                    (Allow, "%s" % self.ticketInstance.seater.uuid, 'seat_ticket'),
                ]

        return acl

    def __init__(self, request, ticket_id):
        self.request = request

        self.ticketInstance = request.db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()

        if self.ticketInstance is None:
            raise HTTPNotFound("Ticket not found")

@view_config(context=TicketInstanceResource, name='', request_method='GET', renderer='json', permission='view_ticket')
def get_ticket(context, request):
    return context.ticketInstance


@view_config(context=TicketInstanceResource, name='seat', request_method='PUT', renderer='json', permission='seat_ticket')
@validate(json_body={'seat_uuid': str})
def seat_ticket(context, request):
    seat = request.db.query(Seat).filter(Seat.uuid == request.json_body['seat_uuid']).first()
    event = get_current_event(request)

    seating_time = event.booking_time + timedelta(seconds=event.seating_time_delta)

    if not context.ticketInstance.ticket_type.seatable:
        request.response.status = 400
        return {
            'error': 'You cannot seat an unseatable ticket'
        }

    if datetime.now() < seating_time:
        request.response.status = 400
        return {
            'error': "You cannot seat your ticket yet(%s < %s)" % (datetime.now(), seating_time)
        }

    if seat is None:
        request.response.status = 404
        return {
            'error': 'Seat not found'
        }
    
    if seat.ticket is not None:
        request.response.status = 400
        return {
            'error': "Someone has already seated there"
        }

    context.ticketInstance.seat = seat
    return context.ticketInstance


@view_config(context=TicketInstanceResource, name='check_in', request_method='POST', renderer='json', permission='check_in')
def check_in_ticket(context, request):
    if context.ticketInstance.checked_in is not None:
        request.response.status = 400;
        return {
            'error': "Ticket already checked in"
        }
    else:
        context.ticketInstance.checked_in = datetime.now()
        return context.ticketInstance

@view_config(context=TicketInstanceResource, name='seater', request_method='PUT', renderer='json', permission='set_seater')
def set_seater(context, request):
    if 'user_email' not in request.json_body:
        seater = request.user
    else:
        seater = request.db.query(User).filter(User.email == request.json_body['user_email'].lower()).first()
    if seater is None:
        request.response.status = 404
        return {
            'error': "User not found"
        }
    
    context.ticketInstance.seater = seater

    return context.ticketInstance


@view_config(context=TicketInstanceResource, name='transfer', request_method='POST', renderer='json', permission='transfer_ticket')
@validate(json_body={'user_email': str})
def transfer_ticket(context, request):
    transfer_target = request.db.query(User).filter(User.email == request.json_body['user_email'].lower()).first()
    if transfer_target is None:
        request.response.status = 404
        return {
            'error': "User not found"
        }

    expiry_offset = int(request.registry.settings['ticket.transfer.expiry'])
    expiry_time = datetime.now() - timedelta(seconds=expiry_offset)

    existing_transfer = request.db.query(TicketTransfer).filter(and_(
        TicketTransfer.ticket == context.ticketInstance,
        TicketTransfer.created > expiry_time)).first()
    if existing_transfer is not None and not existing_transfer.reverted:
        request.response.status = 400
        return {
            'error': "The ticket can still be returned to the original owner, so you cannot transfer it further"
        }
    
    transfer = TicketTransfer(request.user, transfer_target, context.ticketInstance)
    request.db.add(transfer)
    context.ticketInstance.owner = transfer_target
    request.db.flush()

    request.service_manager.get_service('email').send_mail(request.user.email, "Du har overført en billett", "ticket_transferred_to_sender.jinja2", {
        "mail": request.registry.settings["api.contact"],
        "name": request.registry.settings["api.name"],
        "domain": request.registry.settings["api.mainpage"],
        "recipient": transfer_target,
        "hours": expiry_offset/60/60,
        "ticket": context.ticketInstance
    })

    request.service_manager.get_service('email').send_mail(transfer_target.email, "Du har blitt overført en billett", "ticket_transferred_to_recipient.jinja2", {
        "mail": request.registry.settings["api.contact"],
        "name": request.registry.settings["api.name"],
        "domain": request.registry.settings["api.mainpage"],
        "sender": request.user,
        "hours": expiry_offset/60/60,
        "ticket": context.ticketInstance
    })

    return transfer


@view_config(context=TicketInstanceResource, name='transfer_log', request_method='GET', renderer='json', permission='view_ticket_transfer_log')
def transfer_log(context, request):
    return request.db.query(TicketTransfer).filter(TicketTransfer.ticket == context.ticketInstance).all()
