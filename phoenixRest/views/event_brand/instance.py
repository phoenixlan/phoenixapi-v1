from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPNotFound,
    HTTPBadRequest
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow

from phoenixRest.models.core.event_brand import EventBrand
from phoenixRest.models.core.event import Event, get_current_event
from phoenixRest.models.tickets.seatmap import Seatmap
from phoenixRest.models.tickets.ticket_type import TicketType

from phoenixRest.roles import ADMIN, BRAND_ADMIN, TICKET_ADMIN
from phoenixRest.utils import validate

from datetime import datetime

class EventBrandInstanceResource(object):
    def __acl__(self):
        acl = [
            (Allow, Everyone, 'get'),
            (Allow, Everyone, 'get_current_event'),
            (Allow, ADMIN(), 'create_event'),
            (Allow, BRAND_ADMIN(self.eventBrandInstance.uuid), 'create_event'),
            (Allow, ADMIN(), 'create_ticket_type'),
            (Allow, BRAND_ADMIN(self.eventBrandInstance.uuid), 'create_ticket_type'),
            (Allow, TICKET_ADMIN(self.eventBrandInstance.uuid), 'create_ticket_type'),
            (Allow, ADMIN(), 'get_all_seatmaps'),
            (Allow, TICKET_ADMIN(self.eventBrandInstance.uuid), 'get_all_seatmaps'),
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

@view_config(context=EventBrandInstanceResource, name='event', request_method='PUT', renderer='json', permission='create_event')
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

    if len(error) > 0:
        request.response.status = 400
        return {
            "error": ",".join(error)
        }

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
        event_brand=context.eventBrandInstance
    )

    request.db.add(event)
    request.db.flush()
    return event


@view_config(context=EventBrandInstanceResource, name='ticket_type', request_method='POST', renderer='json', permission='create_ticket_type')
@validate(json_body={'name': str, 'price': int, 'refundable': bool, 'grants_admission': bool, 'seatable': bool, 'description': str})
def create_ticket_type(context, request):
    ticket_type = TicketType(
        request.json_body['name'],
        request.json_body['price'],
        request.json_body['description'],
        request.json_body['refundable'],
        request.json_body['seatable'],
        request.json_body['grants_admission']
    )
    ticket_type.event_brand = context.eventBrandInstance
    request.db.add(ticket_type)
    request.db.flush()
    return ticket_type

@view_config(context=EventBrandInstanceResource, name='seatmap', request_method='GET', renderer='json', permission='get_all_seatmaps')
def get_all_seatmaps(context, request):
    return request.db.query(Seatmap) \
        .filter(Seatmap.event_brand_uuid == context.eventBrandInstance.uuid) \
        .order_by(Seatmap.name) \
        .all()
