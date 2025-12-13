from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow


from phoenixRest.models.core.event_brand import EventBrand

from phoenixRest.utils import validate
from phoenixRest.resource import resource
from phoenixRest.views.event_brand.instance import EventBrandInstanceResource

from phoenixRest.roles import ADMIN

import logging
log = logging.getLogger(__name__)


@resource(name='event_brand')
class EventBrandResource(object):
    __acl__ = [
        (Allow, Everyone, 'get'),
        (Allow, ADMIN, 'create'),
    ]
    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        node = EventBrandInstanceResource(self.request, key)
        node.__parent__ = self
        node.__name__ = key
        return node

@view_config(context=EventBrandResource, request_method='GET', renderer='json', permission='get')
def get_event_brands(context, request):
    # Find all events and sort them by start time
    event_types = request.db.query(EventBrand).all()
    return event_types

@view_config(context=EventBrandResource, request_method='POST', renderer='json', permission='create')
@validate(json_body={'name': str})
def create_event_brand(context, request):
    # Find all events and sort them by start time
    brand = EventBrand(request.json_body['name'])

    request.db.add(brand)
    request.db.flush()

    return brand
