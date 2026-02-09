from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow


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
    return get_current_event(request)

@view_config(context=EventViews, request_method='GET', renderer='json', permission='get')
def get_events(request):
    # Find all events and sort them by start time
    events = request.db.query(Event).order_by(Event.start_time.asc()).all()
    return events

@view_config(context=EventViews, request_method='PUT', renderer='json', permission='create')
@validate(json_body={'booking_time': int, 'priority_seating_time_delta': int, 'seating_time_delta': int, 'start_time': int, 'end_time': int, 'name': str, 'max_participants': int})
def create_event(context, request):

    # Create an error list
    error = list()

    if request.json_body['name'] is not None:
        name = request.json_body['name']
        if type(name) != str:
            error.append("Invalid type of name (not string)")

    if request.json_body['start_time'] is not None:
        local_start_time = request.json_body['start_time']
        try:
            start_time = datetime.fromtimestamp(local_start_time)
        except:
            request.response.status = 400
            error.append("Invalid type of start_time format (cannot convert to datetime from integer)")

    if request.json_body['end_time'] is not None:
        local_end_time = request.json_body['end_time']
        try:
            end_time = datetime.fromtimestamp(local_end_time)
        except:
            request.response.status = 400
            error.append("Invalid type of end_time format (cannot convert to datetime from integer)")

    if request.json_body['booking_time'] is not None:
        local_booking_time = request.json_body['booking_time']
        try:
            booking_time = datetime.fromtimestamp(local_booking_time)
        except:
            request.response.status = 400
            error.append("Invalid type of booking_time format (cannot convert to datetime from integer)")
    
    if request.json_body['seating_time_delta'] is not None:
        seating_time_delta = request.json_body['seating_time_delta']
        if type(seating_time_delta) != int:
            error.append("Invalid type of seating_time_delta (not integer)")

    if request.json_body['max_participants'] is not None:
        max_participants = request.json_body['max_participants']
        if type(max_participants) != int:
            error.append("Invalid type of max_participants (not integer)")
            
    if request.json_body['priority_seating_time_delta'] is not None:
        priority_seating_time_delta = request.json_body['priority_seating_time_delta']
        if type(priority_seating_time_delta) != int:
            error.append("Invalid type of priority_seating_time_delta (not integer)")

    participant_age_limit_inclusive = None
    if 'participant_age_limit_inclusive' in request.json_body:
        participant_age_limit_inclusive = request.json_body['participant_age_limit_inclusive']
        if type(participant_age_limit_inclusive) != int:
            error.append("Invalid type of participant_age_limit_inclusive (not integer)")

    crew_age_limit_inclusive = None
    if 'crew_age_limit_inclusive' in request.json_body:
        crew_age_limit_inclusive = request.json_body['crew_age_limit_inclusive']
        if type(crew_age_limit_inclusive) != int:
            error.append("Invalid type of crew_age_limit_inclusive (not integer)")

    theme = None
    if 'theme' in request.json_body:
        theme = request.json_body['theme']
        if type(theme) != str:
            error.append("Invalid type of theme (not string)")

    location_uuid = None
    if 'location_uuid' in request.json_body:
        location_uuid = request.json_body['location_uuid']
        if type(location_uuid) != str:
            error.append("Invalid type of location_uuid (not string)")

    seatmap_uuid = None
    if 'seatmap_uuid' in request.json_body:
        seatmap_uuid = request.json_body['seatmap_uuid']
        if type(seatmap_uuid) != str:
            error.append("Invalid type of seatmap_uuid (not string)")

    event = Event(
        name=name,
        start_time=start_time, 
        end_time=end_time,
        booking_time = booking_time,
        priority_seating_time_delta=priority_seating_time_delta,
        seating_time_delta=seating_time_delta,
        max_participants=max_participants,
        participant_age_limit_inclusive=participant_age_limit_inclusive,
        crew_age_limit_inclusive=crew_age_limit_inclusive,
        theme=theme,
        location_uuid=location_uuid,
        seatmap_uuid=seatmap_uuid,
    )

    request.db.add(event)
    request.db.flush()
    return event

@view_config(context=EventViews, name='current', request_method='OPTIONS', renderer='string', permission='current::get')
def token_options(request):
    return ""
