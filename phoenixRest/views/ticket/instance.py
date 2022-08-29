from operator import and_
from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPNotFound,
    HTTPBadRequest
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow

from phoenixRest.models import db
from phoenixRest.models.core.user import User
from phoenixRest.models.tickets.ticket_transfer import TicketTransfer
from phoenixRest.models.tickets.ticket import Ticket
from phoenixRest.models.tickets.seat import Seat

from phoenixRest.roles import ADMIN, TICKET_ADMIN

from phoenixRest.utils import validate, validateUuidAndQuery
from phoenixRest.resource import resource

from sqlalchemy import and_

from datetime import datetime, timedelta

import logging
log = logging.getLogger(__name__)


class TicketInstanceResource(object):
    def __acl__(self):
        acl = [
            (Allow, ADMIN, 'view_ticket'),
            (Allow, TICKET_ADMIN, 'view_ticket'),
            (Allow, ADMIN, 'seat_ticket'),
            (Allow, TICKET_ADMIN, 'seat_ticket'),
        ]
        if self.ticketInstance is not None:
            acl = acl + [
                # Ticket owner can view their own ticket
                (Allow, "%s" % self.ticketInstance.owner.uuid, 'view_ticket'),
                # Ticket owner can transfer their ticket
                (Allow, "%s" % self.ticketInstance.owner.uuid, 'transfer_ticket'),

                # Ticket owner can seat their own ticket
                (Allow, "%s" % self.ticketInstance.owner.uuid, 'seat_ticket'),
            ]

        return acl

    def __init__(self, request, ticket_id):
        self.request = request

        self.ticketInstance = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()

        if self.ticketInstance is None:
            raise HTTPNotFound("Ticket not found")

@view_config(context=TicketInstanceResource, name='', request_method='GET', renderer='json', permission='view_ticket')
def get_ticket(context, request):
    return context.ticketInstance


@view_config(context=TicketInstanceResource, name='seat', request_method='PUT', renderer='json', permission='seat_ticket')
@validate(json_body={'seat_uuid': str})
def seat_ticket(context, request):
    seat = db.query(Seat).filter(Seat.uuid == request.json_body['seat_uuid']).first()
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

@view_config(context=TicketInstanceResource, name='transfer', request_method='POST', renderer='json', permission='transfer_ticket')
@validate(json_body={'user_email': str})
def transfer_ticket(context, request):
    transfer_target = db.query(User).filter(User.email == request.json_body['user_email']).first()
    if transfer_target is None:
        request.response.status = 404
        return {
            'error': "User not found"
        }

    expiry_offset = int(request.registry.settings['ticket.transfer.expiry'])
    expiry_time = datetime.now() - timedelta(seconds=expiry_offset)

    existing_transfer = db.query(TicketTransfer).filter(and_(
        TicketTransfer.ticket == context.ticketInstance,
        TicketTransfer.created > expiry_time)).first()
    if existing_transfer is not None:
        request.response.status = 400
        return {
            'error': "The ticket can still be returned to the original owner, so you cannot transfer it further"
        }
    
    transfer = TicketTransfer(request.user, transfer_target, context.ticketInstance)
    db.add(transfer)
    context.ticketInstance.owner = transfer_target
    db.flush()
    return transfer




