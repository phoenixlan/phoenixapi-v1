from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow


from phoenixRest.models.core.event_brand import EventBrand

from phoenixRest.resource import resource

from phoenixRest.roles import ADMIN

import logging
log = logging.getLogger(__name__)


@view_defaults(context='.EventBrandResource')
@resource(name='event_brand')
class EventBrandResource(object):
    __acl__ = [
        (Allow, Everyone, 'get'),
        (Allow, ADMIN, 'create'),
    ]
    def __init__(self, request):
        self.request = request
        log.info("event type class init")

@view_config(context=EventBrandResource, request_method='GET', renderer='json', permission='get')
def get_event_types(request):
    # Find all events and sort them by start time
    event_types = request.db.query(EventBrand).all()
    return event_types
