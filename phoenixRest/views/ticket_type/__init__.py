from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow

from phoenixRest.models.tickets.ticket_type import TicketType

from phoenixRest.utils import validate
from phoenixRest.resource import resource

from phoenixRest.roles import ADMIN

from phoenixRest.views.seatmap.instance import SeatmapInstanceViews

from datetime import datetime

import logging
log = logging.getLogger(__name__)

@resource(name='ticketType')
class TicketTypeResource(object):
    __acl__ = [
        # Don't allow anyone to fetch ticket types from here
        # Anyone could use the event-specific endpoint instead.
        (Allow, ADMIN(), 'getAll'),
        (Allow, ADMIN(), 'create'),

        # Authenticated pages
        #(Allow, Authenticated, Authenticated),
        #(Deny, Everyone, Authenticated),
    ]
    def __init__(self, request):
        self.request = request

@view_config(name='', context=TicketTypeResource, request_method='GET', renderer='json', permission='getAll')
def get_all_ticket_types(context, request):
    return request.db.query(TicketType).order_by(TicketType.name).all()

