from phoenixRest.roles import CREW_CARD_PRINTER
from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPNotFound,
    HTTPBadRequest
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow

from phoenixRest.models.core.event import Event
from phoenixRest.models.core.agenda_entry import AgendaEntry
from phoenixRest.models.core.user import User
from phoenixRest.models.crew.application import Application
from phoenixRest.models.crew.card_order import CardOrder
from phoenixRest.models.crew.application_crew_mapping import ApplicationCrewMapping
from phoenixRest.models.tickets.ticket import Ticket
from phoenixRest.models.tickets.row import Row
from phoenixRest.models.tickets.seatmap import Seatmap
from phoenixRest.models.tickets.ticket_type import TicketType

from phoenixRest.views.event.agenda import EventAgendaResource
from phoenixRest.views.event.application import EventApplicationResource
from phoenixRest.views.event.card_order import EventCardOrderResource
from phoenixRest.views.event.position_mapping import EventPositionMappingResource
from phoenixRest.views.event.store_session import EventStoreSessionResource
from phoenixRest.views.event.ticket import EventTicketResource

from phoenixRest.mappers.user import map_user_simple_with_secret_fields

from phoenixRest.roles import ADMIN, BRAND_ADMIN, CHIEF, HR_ADMIN, TICKET_ADMIN

from phoenixRest.utils import validate

from sqlalchemy import and_
from sqlalchemy.orm import joinedload

from datetime import datetime

import logging
log = logging.getLogger(__name__)

class EventInstanceResource(dict):
    def __acl__(self):
        acl = [
            (Allow, Everyone, 'event_get'),
            (Allow, ADMIN(), 'event_get'),
            (Allow, BRAND_ADMIN(self.eventInstance.event_brand_uuid), 'event_get'),

            (Allow, Everyone, 'event_ticket_type_get'),
            (Allow, ADMIN(), 'event_ticket_type_get'),
            (Allow, BRAND_ADMIN(self.eventInstance.event_brand_uuid), 'event_ticket_type_get'),

            (Allow, Everyone, 'ticket_availability_get'),

            (Allow, ADMIN(), 'event_memberships_get'),
            (Allow, TICKET_ADMIN(self.eventInstance.event_brand_uuid), 'event_memberships_get'),
            (Allow, HR_ADMIN(self.eventInstance.event_brand_uuid), 'event_memberships_get'),

            (Allow, ADMIN(), 'add_ticket_type'),
            (Allow, TICKET_ADMIN(self.eventInstance.event_brand_uuid), 'add_ticket_type'),

            (Allow, CHIEF(self.eventInstance.event_brand_uuid), 'applications_get'),
            (Allow, ADMIN(), 'applications_get'),

            (Allow, CHIEF(self.eventInstance.event_brand_uuid), 'list_card_orders'),
            (Allow, ADMIN(), 'list_card_orders'),
            (Allow, CREW_CARD_PRINTER(self.eventInstance.event_brand_uuid), 'list_card_orders'),

            (Allow, Everyone, 'list_agenda_entries'),

            (Allow, ADMIN(), 'event_update'),

            (Allow, CHIEF(self.eventInstance.event_brand_uuid), 'applications_get'),
            (Allow, ADMIN(), 'applications_get'),

            (Allow, ADMIN(), 'event_edit'),
            (Allow, BRAND_ADMIN(self.eventInstance.event_brand_uuid), 'event_edit'),

        ]
        return acl

    def __init__(self, request, uuid):
        self.request = request
        self.eventInstance = request.db.query(Event).filter(Event.uuid == uuid).first()

        if self.eventInstance is None:
            raise HTTPNotFound("Event not found")

        self["agenda"] = EventAgendaResource(request, self.eventInstance)
        self["application"] = EventApplicationResource(request, self.eventInstance)
        self["card_order"] = EventCardOrderResource(request, self.eventInstance)
        self["position_mapping"] = EventPositionMappingResource(request, self.eventInstance)
        self["store_session"] = EventStoreSessionResource(request, self.eventInstance)
        self["ticket"] = EventTicketResource(request, self.eventInstance)

@view_config(context=EventInstanceResource, name='', request_method='GET', renderer='json', permission='event_get')
def get_event(context, request):
    return context.eventInstance

@view_config(context=EventInstanceResource, name='', request_method='PATCH', renderer='json', permission='event_update')
def update_event(context, request):
    # Validate and update fields that are present in the request body
    if not hasattr(request, 'json_body') or not request.json_body:
        request.response.status = 400
        return {
            'error': 'Request body must be JSON'
        }

    event = context.eventInstance
    body = request.json_body

    # Collect timestamp values for cross-field validation
    new_booking_time = None
    new_start_time = None
    new_end_time = None

    # Non-relation fields with validation
    if 'name' in body:
        if not isinstance(body['name'], str) or not body['name'].strip():
            request.response.status = 400
            return {'error': 'name must be a non-empty string'}
        event.name = body['name']

    if 'booking_time' in body:
        if not isinstance(body['booking_time'], int) or body['booking_time'] < 0:
            request.response.status = 400
            return {'error': 'booking_time must be a non-negative Unix timestamp (integer)'}
        new_booking_time = datetime.fromtimestamp(body['booking_time'])
        event.booking_time = new_booking_time

    if 'priority_seating_time_delta' in body:
        if not isinstance(body['priority_seating_time_delta'], int) or body['priority_seating_time_delta'] < 0:
            request.response.status = 400
            return {'error': 'priority_seating_time_delta must be a non-negative integer (seconds)'}
        event.priority_seating_time_delta = body['priority_seating_time_delta']

    if 'seating_time_delta' in body:
        if not isinstance(body['seating_time_delta'], int) or body['seating_time_delta'] < 0:
            request.response.status = 400
            return {'error': 'seating_time_delta must be a non-negative integer (seconds)'}
        event.seating_time_delta = body['seating_time_delta']

    if 'start_time' in body:
        if not isinstance(body['start_time'], int) or body['start_time'] < 0:
            request.response.status = 400
            return {'error': 'start_time must be a non-negative Unix timestamp (integer)'}
        new_start_time = datetime.fromtimestamp(body['start_time'])
        event.start_time = new_start_time

    if 'end_time' in body:
        if not isinstance(body['end_time'], int) or body['end_time'] < 0:
            request.response.status = 400
            return {'error': 'end_time must be a non-negative Unix timestamp (integer)'}
        new_end_time = datetime.fromtimestamp(body['end_time'])
        event.end_time = new_end_time

    if 'theme' in body:
        if body['theme'] is not None and not isinstance(body['theme'], str):
            request.response.status = 400
            return {'error': 'theme must be a string or null'}
        event.theme = body['theme']

    if 'max_participants' in body:
        if not isinstance(body['max_participants'], int) or body['max_participants'] <= 0:
            request.response.status = 400
            return {'error': 'max_participants must be a positive integer'}
        event.max_participants = body['max_participants']

    if 'participant_age_limit_inclusive' in body:
        if not isinstance(body['participant_age_limit_inclusive'], int) or body['participant_age_limit_inclusive'] < -1:
            request.response.status = 400
            return {'error': 'participant_age_limit_inclusive must be an integer >= -1 (-1 means not applicable)'}
        event.participant_age_limit_inclusive = body['participant_age_limit_inclusive']

    if 'crew_age_limit_inclusive' in body:
        if not isinstance(body['crew_age_limit_inclusive'], int) or body['crew_age_limit_inclusive'] < -1:
            request.response.status = 400
            return {'error': 'crew_age_limit_inclusive must be an integer >= -1 (-1 means not applicable)'}
        event.crew_age_limit_inclusive = body['crew_age_limit_inclusive']

    if 'cancellation_reason' in body:
        if body['cancellation_reason'] is not None and not isinstance(body['cancellation_reason'], str):
            request.response.status = 400
            return {'error': 'cancellation_reason must be a string or null'}
        event.cancellation_reason = body['cancellation_reason']

    # Seatmap relation - verify it exists
    if 'seatmap_uuid' in body:
        if body['seatmap_uuid'] is not None:
            seatmap = request.db.query(Seatmap).filter(Seatmap.uuid == body['seatmap_uuid']).first()
            if not seatmap:
                request.response.status = 400
                return {'error': 'Seatmap not found'}
            if seatmap.event_brand_uuid != event.event_brand_uuid:
                request.response.status = 400
                return {'error': 'Seatmap belongs to a different event brand'}
            event.seatmap = seatmap
        else:
            event.seatmap = None

    # Cross-field validation for timestamps
    booking_time = new_booking_time if new_booking_time else event.booking_time
    start_time = new_start_time if new_start_time else event.start_time
    end_time = new_end_time if new_end_time else event.end_time

    if booking_time >= start_time:
        request.response.status = 400
        return {'error': 'booking_time must be before start_time'}

    if start_time >= end_time:
        request.response.status = 400
        return {'error': 'start_time must be before end_time'}

    request.db.flush()
    return event

# Objects relating to the specific event
@view_config(context=EventInstanceResource, name='applications', request_method='GET', renderer='json', permission='applications_get')
def get_all_applications(context, request):
    # TODO get for multiple applications
    # Find all applications and sort them by time created
    applications = request.db \
        .query(Application) \
        .filter(Application.event_uuid == context.eventInstance.uuid) \
        .options(joinedload(Application.user)) \
        .options(joinedload(Application.event)) \
        .options(joinedload(Application.crews).joinedload(ApplicationCrewMapping.crew)) \
        .order_by(Application.created.asc()).all()

    return applications

@view_config(context=EventInstanceResource, name='ticket', request_method='GET', renderer='json', permission='event_tickets_get')
def get_tickets(context, request):
    tickets = request.db.query(Ticket).filter(Ticket.event_uuid == context.eventInstance.uuid).order_by(Ticket.ticket_id).options(joinedload(Ticket.owner), joinedload(Ticket.buyer), joinedload(Ticket.seater), joinedload(Ticket.ticket_type), joinedload(Ticket.payment), joinedload(Ticket.seat)).all()
    return tickets

@view_config(context=EventInstanceResource, name='new_memberships', request_method='GET', renderer='json', permission='event_memberships_get')
def get_new_memberships(context, request):
    users = request.db.query(User).join(Ticket, Ticket.owner_uuid == User.uuid).join(TicketType, Ticket.ticket_type_uuid==TicketType.uuid).filter(and_(Ticket.event_uuid == context.eventInstance.uuid, TicketType.grants_membership == True)).all()
    return [ map_user_simple_with_secret_fields(user, request) for user in users ]

@view_config(context=EventInstanceResource, name='ticket_availability', request_method='GET', renderer='json', permission='ticket_availability_get')
def get_ticket_availability(context, request):
    return {
        'total': max(context.eventInstance.get_total_ticket_availability(request), 0)
    }

@view_config(name='ticketType', context=EventInstanceResource, request_method='PUT', renderer='json', permission='add_ticket_type')
@validate(json_body={'ticket_type_uuid': str})
def add_ticket_type(context, request):
    ticket_type = request.db.query(TicketType).filter(TicketType.uuid == request.json_body['ticket_type_uuid']).first()
    if not ticket_type:
        request.response.status = 404
        return {
            'error': "Ticket type not found"
        }
    if ticket_type in context.eventInstance.static_ticket_types:
        return context.eventInstance
    context.eventInstance.static_ticket_types.append(ticket_type)
    return context.eventInstance

@view_config(context=EventInstanceResource, name='ticketType', request_method='GET', renderer='json', permission='event_ticket_type_get')
def get_ticket_types(context, request):
    # Ticket types deduced through rows configured to only allow them
    row_types = request.db.query(TicketType) \
        .join(Row, TicketType.uuid == Row.ticket_type_uuid) \
        .join(Seatmap, Row.seatmap_uuid == Seatmap.uuid) \
        .join(Event, Event.seatmap_uuid == Seatmap.uuid) \
        .filter(Event.uuid == context.eventInstance.uuid).all()

    # Ticket types assigned to the event
    static_types = context.eventInstance.static_ticket_types
    return list(set(row_types+static_types))

# Get all card orders for specified or current event
@view_config(name="card_orders", context=EventInstanceResource, request_method="GET", renderer="json", permission="list_card_orders")
def get_card_orders(context, request):
    # We either get the specified event or the current event
    return request.db.query(CardOrder).filter(CardOrder.event == context.eventInstance).all()

@view_config(name='edit', context=EventInstanceResource, request_method='PATCH', renderer='json', permission='event_edit')
def edit_event(context, request):

    error = list()

    update_name = False
    if 'name' in request.json_body:
        if type(request.json_body['name']) != str:
            error.append("Failed to update name, invalid type (not string)")
        update_name = True

    update_start_time = False
    if 'start_time' in request.json_body:
        try:
            start_time = datetime.fromtimestamp(request.json_body['start_time'])
            update_start_time = True
        except:
            error.append("Failed to update start_time, invalid format (cannot convert to datetime from integer)")

    update_end_time = False
    if 'end_time' in request.json_body:
        try:
            end_time = datetime.fromtimestamp(request.json_body['end_time'])
            update_end_time = True
        except:
            error.append("Failed to update end_time, invalid format (cannot convert to datetime from integer)")

    update_booking_time = False
    if 'booking_time' in request.json_body:
        try:
            booking_time = datetime.fromtimestamp(request.json_body['booking_time'])
            update_booking_time = True
        except:
            error.append("Failed to update booking_time, invalid format (cannot convert to datetime from integer)")

    update_priority_seating_time_delta = False
    if 'priority_seating_time_delta' in request.json_body:
        if type(request.json_body['priority_seating_time_delta']) != int:
            error.append("Failed to update priority_seating_time_delta, invalid type (not integer)")
        update_priority_seating_time_delta = True

    update_seating_time_delta = False
    if 'seating_time_delta' in request.json_body:
        if type(request.json_body['seating_time_delta']) != int:
            error.append("Failed to update seating_time_delta, invalid type (not integer)")
        update_seating_time_delta = True

    update_max_participants = False
    if 'max_participants' in request.json_body:
        if type(request.json_body['max_participants']) != int:
            error.append("Failed to update max_participants, invalid type (not integer)")
        update_max_participants = True

    update_participant_age_limit_inclusive = False
    if 'participant_age_limit_inclusive' in request.json_body:
        if type(request.json_body['participant_age_limit_inclusive']) != int:
            error.append("Failed to update participant_age_limit_inclusive, invalid type (not integer)")
        update_participant_age_limit_inclusive = True

    update_crew_age_limit_inclusive = False
    if 'crew_age_limit_inclusive' in request.json_body:
        if type(request.json_body['crew_age_limit_inclusive']) != int:
            error.append("Failed to update crew_age_limit_inclusive, invalid type (not integer)")
        update_crew_age_limit_inclusive = True

    update_theme = False
    if 'theme' in request.json_body:
        if request.json_body['theme'] is not None:
            if type(request.json_body['theme']) != str:
                error.append("Failed to update theme, invalid type (not string or None)")
        update_theme = True

    update_location_uuid = False
    if 'location_uuid' in request.json_body:
        if request.json_body['location_uuid'] is not None:
            if type(request.json_body['location_uuid']) != str:
                error.append("Failed to update location_uuid, invalid type (not string or None)")
        update_location_uuid = True

    update_seatmap_uuid = False
    if 'seatmap_uuid' in request.json_body:
        if request.json_body['seatmap_uuid'] is not None:
            if type(request.json_body['seatmap_uuid']) != str:
                error.append("Failed to update seatmap_uuid, invalid type (not string or None)")
        update_seatmap_uuid = True

    update_cancellation_reason = False
    if 'cancellation_reason' in request.json_body:
        if request.json_body['cancellation_reason'] is not None:
            if type(request.json_body['cancellation_reason']) != str:
                error.append("Failed to update cancellation_reason, invalid type (not string or None)")
        update_cancellation_reason = True

    if len(error) > 0:
        request.response.status = 400
        return {
            'error': 'An error occured in one or more fields when attempting to update event information',
            'data': error
        }
    
    if update_name is True:
        context.eventInstance.name = request.json_body['name']

    if update_start_time is True:
        context.eventInstance.start_time = start_time

    if update_end_time is True:
        context.eventInstance.end_time = end_time

    if update_booking_time is True:
        context.eventInstance.booking_time = booking_time

    if update_priority_seating_time_delta is True:
        context.eventInstance.priority_seating_time_delta = request.json_body['priority_seating_time_delta']
    
    if update_seating_time_delta is True:
        context.eventInstance.seating_time_delta = request.json_body['seating_time_delta']
    
    if update_max_participants is True:
        context.eventInstance.max_participants = request.json_body['max_participants']
    
    if update_participant_age_limit_inclusive is True:
        context.eventInstance.participant_age_limit_inclusive = request.json_body['participant_age_limit_inclusive']
    
    if update_crew_age_limit_inclusive is True:
        context.eventInstance.crew_age_limit_inclusive = request.json_body['crew_age_limit_inclusive']
    
    if update_theme is True:
        context.eventInstance.theme = request.json_body['theme']
    
    if update_location_uuid is True:
        context.eventInstance.location_uuid = request.json_body['location_uuid']
    
    if update_seatmap_uuid is True:
        context.eventInstance.seatmap_uuid = request.json_body['seatmap_uuid']
    
    if update_cancellation_reason is True:
        context.eventInstance.cancellation_reason = request.json_body['cancellation_reason']
    
    return {
        'info': 'Event information updated successfully',
        'data': context.eventInstance
    }
