from phoenixRest.resource import resource

from phoenixRest.views.position_mapping.instance import PositionMappingInstanceResource

import logging
log = logging.getLogger(__name__)


@resource(name='position_mapping')
class PositionMappingResource(object):
    __acl__ = []
    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        node = PositionMappingInstanceResource(self.request, key)
        node.__parent__ = self
        node.__name__ = key
        return node
