from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPNotFound,
    HTTPBadRequest
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow

from phoenixRest.models.core.event import Event
from phoenixRest.models.core.user import User
from phoenixRest.models.crew.application import Application
from phoenixRest.models.crew.application_crew_mapping import ApplicationCrewMapping
from phoenixRest.models.tickets.ticket import Ticket
from phoenixRest.models.tickets.row import Row
from phoenixRest.models.tickets.seatmap import Seatmap
from phoenixRest.models.tickets.ticket_type import TicketType

from phoenixRest.mappers.user import map_user_simple_with_secret_fields

from phoenixRest.roles import ADMIN, EVENT_ADMIN, CHIEF, HR_ADMIN, TICKET_ADMIN, TICKET_CHECKIN

from phoenixRest.utils import validate

from sqlalchemy import and_
from sqlalchemy.orm import joinedload

from datetime import datetime

import logging
log = logging.getLogger(__name__)

class EventInstanceResource(object):
    def __acl__(self):
        acl = [
            (Allow, Everyone, 'event_get'),
            (Allow, ADMIN, 'event_get'),
            (Allow, EVENT_ADMIN, 'event_get'),

            (Allow, Everyone, 'event_ticket_type_get'),
            (Allow, ADMIN, 'event_ticket_type_get'),
            (Allow, EVENT_ADMIN, 'event_ticket_type_get'),

            (Allow, Everyone, 'ticket_availability_get'),

            (Allow, ADMIN, 'event_tickets_get'),
            (Allow, TICKET_ADMIN, 'event_tickets_get'),
            (Allow, TICKET_CHECKIN, 'event_tickets_get'),

            (Allow, ADMIN, 'event_memberships_get'),
            (Allow, TICKET_ADMIN, 'event_memberships_get'),
            (Allow, HR_ADMIN, 'event_memberships_get'),

            (Allow, ADMIN, 'add_ticket_type'),
            (Allow, TICKET_ADMIN, 'add_ticket_type'),

            (Allow, CHIEF, 'applications_get'),
            (Allow, ADMIN, 'applications_get'),

            (Allow, ADMIN, 'event_edit'),
            (Allow, EVENT_ADMIN, 'event_edit'),
        ]
        return acl

    def __init__(self, request, uuid):
        self.request = request
        self.eventInstance = request.db.query(Event).filter(Event.uuid == uuid).first()

        if self.eventInstance is None:
            raise HTTPNotFound("Event not found")

@view_config(context=EventInstanceResource, name='', request_method='GET', renderer='json', permission='event_get')
def get_event(context, request):
    return context.eventInstance

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
    tickets = request.db.query(Ticket).filter(Ticket.event_uuid == context.eventInstance.uuid).order_by(Ticket.ticket_id).all()
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
    
    if update_name is True: context.eventInstance.name = request.json_body['name']
    if update_start_time is True: context.eventInstance.start_time = start_time
    if update_end_time is True: context.eventInstance.end_time = end_time
    if update_booking_time is True: context.eventInstance.booking_time = booking_time
    if update_priority_seating_time_delta is True: context.eventInstance.priority_seating_time_delta = request.json_body['priority_seating_time_delta']
    if update_seating_time_delta is True: context.eventInstance.seating_time_delta = request.json_body['seating_time_delta']
    if update_max_participants is True: context.eventInstance.max_participants = request.json_body['max_participants']
    if update_participant_age_limit_inclusive is True: context.eventInstance.participant_age_limit_inclusive = request.json_body['participant_age_limit_inclusive']
    if update_crew_age_limit_inclusive is True: context.eventInstance.crew_age_limit_inclusive = request.json_body['crew_age_limit_inclusive']
    if update_theme is True: context.eventInstance.theme = request.json_body['theme']
    if update_location_uuid is True: context.eventInstance.location_uuid = request.json_body['location_uuid']
    if update_seatmap_uuid is True: context.eventInstance.seatmap_uuid = request.json_body['seatmap_uuid']
    if update_cancellation_reason is True: context.eventInstance.cancellation_reason = request.json_body['cancellation_reason']
    
    return {
        'info': 'Event information updated successfully',
        'data': context.eventInstance
    }
    

