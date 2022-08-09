from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
)
from pyramid.security import Authenticated, Everyone, Deny, Allow


from phoenixRest.models import db
from phoenixRest.models.core.event import Event, get_current_event

from phoenixRest.utils import validate
from phoenixRest.resource import resource

from phoenixRest.roles import ADMIN

from phoenixRest.views.event.instance import EventInstanceResource

from datetime import datetime

import logging
log = logging.getLogger(__name__)


@view_defaults(context='.EventViews')
@resource(name='event')
class EventViews(object):
    __acl__ = [
        (Allow, Everyone, 'current::get'),
        (Allow, Everyone, 'get'),
        (Allow, ADMIN, 'create'),

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

@view_config(context=EventViews, name='current', request_method='GET', renderer='json', permission='current::get')
def current(request):
    return get_current_event()

@view_config(context=EventViews, request_method='GET', renderer='json', permission='get')
def get_events(request):
    # Find all events and sort them by start time
    events = db.query(Event).order_by(Event.start_time.asc()).all()
    return events

@view_config(context=EventViews, request_method='PUT', renderer='json', permission='create')
@validate(json_body={'start_time': int, 'end_time': int, 'max_participants': int})
def create_event(request):
    event = Event(start_time=datetime.fromtimestamp(request.json_body['start_time']), 
                  end_time=datetime.fromtimestamp(request.json_body['end_time']), 
                  max_participants=request.json_body['max_participants'])
    db.add(event)
    db.flush()
    return event

@view_config(context=EventViews, name='current', request_method='OPTIONS', renderer='string', permission='current::get')
def token_options(request):
    return ""
