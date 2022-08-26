from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPNotFound
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow


from phoenixRest.models import db
from phoenixRest.models.tickets.ticket_type import TicketType
from phoenixRest.models.core.user import User
from phoenixRest.models.tickets.row import Row
from phoenixRest.models.tickets.ticket import Ticket
from phoenixRest.models.core.event import get_current_event

from phoenixRest.utils import validate
from phoenixRest.resource import resource

from phoenixRest.roles import ADMIN, TICKET_ADMIN

from phoenixRest.views.ticket_transfer.instance import TicketTransferInstanceResource

from datetime import datetime

import logging
log = logging.getLogger(__name__)

@resource(name='ticket_transfer')
class TicketTransferResource(object):
    __acl__ = [
    ]
    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        node = TicketTransferInstanceResource(self.request, key)
        node.__parent__ = self
        node.__name__ = key
        return node

