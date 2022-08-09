from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPNotFound
)
from pyramid.security import Authenticated, Everyone, Deny, Allow


from phoenixRest.models import db
from phoenixRest.models.tickets.ticket_type import TicketType
from phoenixRest.models.core.user import User
from phoenixRest.models.tickets.row import Row
from phoenixRest.models.tickets.ticket import Ticket
from phoenixRest.models.core.event import get_current_event

from phoenixRest.utils import validate
from phoenixRest.resource import resource

from phoenixRest.roles import ADMIN, TICKET_ADMIN

from phoenixRest.views.row.instance import RowInstanceResource

from datetime import datetime

import logging
log = logging.getLogger(__name__)

@resource(name='ticket')
class TicketResource(object):
    __acl__ = [
        (Allow, ADMIN, 'getAll'),
        (Allow, TICKET_ADMIN, 'getAll'),
        (Allow, ADMIN, 'create'),
        (Allow, TICKET_ADMIN, 'create'),

        # Authenticated pages
        #(Allow, Authenticated, Authenticated),
        #(Deny, Everyone, Authenticated),
    ]
    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        """Traverse to a specific seatmap item"""
        node = RowInstanceResource(self.request, key)
        node.__parent__ = self
        node.__name__ = key
        return node

@view_config(name='', context=TicketResource, request_method='GET', renderer='json', permission='getAll')
def get_all_tickets(context, request):
    return db.query(Row).order_by(Row.name).all()

@view_config(name='', context=TicketResource, request_method='POST', renderer='json', permission='create')
@validate(json_body={'recipient': str, 'ticket_type': str})
def create_ticket(context, request):
    receiving_user = db.query(User).filter(User.uuid == request.json_body['recipient']).first()
    if not receiving_user:
        raise HTTPNotFound("Recepient user not found")

    ticket_type = db.query(TicketType).filter(TicketType.uuid == request.json_body['ticket_type']).first()
    if ticket_type is None:
        raise HTTPNotFound("Ticket type not found")

    ticket = Ticket(receiving_user, None, ticket_type, get_current_event())
    db.add(ticket)
    db.flush()
    return ticket

