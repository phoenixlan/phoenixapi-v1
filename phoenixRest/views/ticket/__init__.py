from pyramid.view import view_config
from pyramid.authorization import Allow


from phoenixRest.models.tickets.ticket import Ticket
from phoenixRest.resource import resource

from phoenixRest.roles import ADMIN

from phoenixRest.views.ticket.instance import TicketInstanceResource

from sqlalchemy.orm import joinedload
from datetime import datetime

import logging
log = logging.getLogger(__name__)

@resource(name='ticket')
class TicketResource(object):
    __acl__ = [
        (Allow, ADMIN(), 'getAll'),
        # Authenticated pages
        #(Allow, Authenticated, Authenticated),
        #(Deny, Everyone, Authenticated),
    ]
    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        node = TicketInstanceResource(self.request, key)
        node.__parent__ = self
        node.__name__ = key
        return node

@view_config(name='', context=TicketResource, request_method='GET', renderer='json', permission='getAll')
def get_all_tickets(context, request):
    return request.db.query(Ticket).order_by(Ticket.ticket_id).options(joinedload(Ticket.owner), joinedload(Ticket.buyer), joinedload(Ticket.seater), joinedload(Ticket.ticket_type), joinedload(Ticket.payment), joinedload(Ticket.seat)).all()
