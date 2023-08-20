from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow

from phoenixRest.models.core.user import User
from phoenixRest.models.core.event import Event
from phoenixRest.models.tickets.ticket_voucher import TicketVoucher
from phoenixRest.models.tickets.ticket_type import TicketType

from phoenixRest.views.consent_withdrawal_code.instance import ConsentWithdrawalCodeInstanceResource

from phoenixRest.utils import validate
from phoenixRest.resource import resource

from phoenixRest.roles import ADMIN, TICKET_ADMIN

import logging
log = logging.getLogger(__name__)

@resource(name='consent_withdrawal_code')
class ConsentWithdrawalCodeResource(object):
    __acl__ = [
    ]
    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        node = ConsentWithdrawalCodeInstanceResource(self.request, key)
        node.__parent__ = self
        node.__name__ = key
        return node