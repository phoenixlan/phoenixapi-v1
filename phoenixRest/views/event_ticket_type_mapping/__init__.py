from phoenixRest.resource import resource

from phoenixRest.views.event_ticket_type_mapping.instance import EventTicketTypeMappingInstanceResource

import logging
log = logging.getLogger(__name__)


@resource(name='event_ticket_type_mapping')
class EventTicketTypeMappingResource(object):
    __acl__ = []
    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        node = EventTicketTypeMappingInstanceResource(self.request, key)
        node.__parent__ = self
        node.__name__ = key
        return node
