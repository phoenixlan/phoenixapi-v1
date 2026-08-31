from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow


from phoenixRest.models.core.event import Event
from phoenixRest.resource import resource

from phoenixRest.roles import ADMIN

from phoenixRest.views.event.instance import EventInstanceResource

import logging
log = logging.getLogger(__name__)


@view_defaults(context='.EventViews')
@resource(name='event')
class EventViews(object):
    __acl__ = [
        (Allow, Everyone, 'list'),

        # Authenticated pages
        #(Allow, Authenticated, Authenticated),
        #(Deny, Everyone, Authenticated),
    ]
    def __init__(self, request):
        self.request = request
        log.info("event class init")

    def __getitem__(self, key):
        """Traverse to a specific crew item"""
        if key in ['current']:
            raise KeyError('')
        node = EventInstanceResource(self.request, key)
        node.__parent__ = self
        node.__name__ = key
        return node

@view_config(context=EventViews, request_method='GET', renderer='json', permission='list')
def get_events(request):
    # Find all events and sort them by start time
    events = request.db.query(Event).order_by(Event.start_time.asc()).all()
    return events
