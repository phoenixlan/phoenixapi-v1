from pyramid.view import view_config, view_defaults

from phoenixRest.models.tickets.ticket_type import TicketType

from phoenixRest.resource import resource

from phoenixRest.views.ticket_transfer.instance import TicketTransferInstanceResource

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

