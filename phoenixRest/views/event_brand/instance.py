from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPNotFound,
    HTTPBadRequest
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow

from phoenixRest.models.core.event_brand import EventBrand
from phoenixRest.models.core.event import get_current_event

class EventBrandInstanceResource(object):
    def __acl__(self):
        acl = [
            (Allow, Everyone, 'get'),
            (Allow, Everyone, 'get_current_event'),
        ]
        return acl

    def __init__(self, request, uuid):
        self.request = request
        self.eventBrandInstance = request.db.query(EventBrand).filter(EventBrand.uuid == uuid).first()

        if self.eventBrandInstance is None:
            raise HTTPNotFound("Event brand not found")


@view_config(context=EventBrandInstanceResource, name='', request_method='GET', renderer='json', permission='get')
def get_event_brand(context, request):
    return context.eventBrandInstance

@view_config(context=EventBrandInstanceResource, name='current_event', request_method='GET', renderer='json', permission='get_current_event')
def get_active_event(context, request):
    return get_current_event(request.db, context.eventBrandInstance)
