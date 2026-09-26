from phoenixRest.roles import CREW_CARD_PRINTER
from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPNotFound,
    HTTPBadRequest
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow

from phoenixRest.models.core.event import Event, validate_ticket_sales_caps
from phoenixRest.models.core.event_ticket_type_mapping import EventTicketTypeMapping
from phoenixRest.models.core.agenda_entry import AgendaEntry
from phoenixRest.models.core.user import User, EventTicketTypeMappingActivations
from phoenixRest.models.crew.application import Application
from phoenixRest.models.crew.card_order import CardOrder
from phoenixRest.models.crew.application_crew_mapping import ApplicationCrewMapping
from phoenixRest.models.crew.position import Position
from phoenixRest.models.crew.position_mapping import PositionMapping
from phoenixRest.models.tickets.ticket import Ticket
from phoenixRest.models.tickets.ticket_type import TicketType

from phoenixRest.views.event.agenda import EventAgendaResource
from phoenixRest.views.event.application import EventApplicationResource
from phoenixRest.views.event.card_order import EventCardOrderResource
from phoenixRest.views.event.position_mapping import EventPositionMappingResource
from phoenixRest.views.event.store_session import EventStoreSessionResource
from phoenixRest.views.event.ticket import EventTicketResource

from phoenixRest.mappers.user import map_user_with_secret_fields_membership_personalia

from phoenixRest.features.crew_card import generate_badge

from phoenixRest.roles import ADMIN, BRAND_ADMIN, CHIEF, HR_ADMIN, TICKET_ADMIN

from phoenixRest.utils import validate, validateUuidAndQuery

from sqlalchemy import and_, or_, select
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

            (Allow, ADMIN(), 'ticket_type_mapping_list'),
            (Allow, BRAND_ADMIN(self.eventInstance.event_brand_uuid), 'ticket_type_mapping_list'),
            (Allow, TICKET_ADMIN(self.eventInstance.event_brand_uuid), 'ticket_type_mapping_list'),

            (Allow, ADMIN(), 'ticket_type_mapping_create'),
            (Allow, BRAND_ADMIN(self.eventInstance.event_brand_uuid), 'ticket_type_mapping_create'),
            (Allow, TICKET_ADMIN(self.eventInstance.event_brand_uuid), 'ticket_type_mapping_create'),

            (Allow, Authenticated, 'unlock_ticket_type'),

            (Allow, CHIEF(self.eventInstance.event_brand_uuid), 'applications_get'),
            (Allow, ADMIN(), 'applications_get'),

            (Allow, CHIEF(self.eventInstance.event_brand_uuid), 'list_card_orders'),
            (Allow, ADMIN(), 'list_card_orders'),
            (Allow, CREW_CARD_PRINTER(self.eventInstance.event_brand_uuid), 'list_card_orders'),

            # Who can view the crew card of someone attending this event?
            (Allow, ADMIN(), 'get_crew_card'),
            (Allow, CHIEF(self.eventInstance.event_brand_uuid), 'get_crew_card'),
            (Allow, CREW_CARD_PRINTER(self.eventInstance.event_brand_uuid), 'get_crew_card'),

            (Allow, Everyone, 'list_agenda_entries'),

            (Allow, ADMIN(), 'event_edit'),
            (Allow, BRAND_ADMIN(self.eventInstance.event_brand_uuid), 'event_edit'),

        ]
        return acl

    def __init__(self, request, uuid):
        self.request = request
        self.eventInstance = validateUuidAndQuery(request, Event, Event.uuid, uuid)

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
    users = request.db.query(User).join(Ticket, Ticket.owner_uuid == User.uuid) \
        .join(TicketType, Ticket.ticket_type_uuid==TicketType.uuid) \
        .filter(and_(Ticket.event_uuid == context.eventInstance.uuid, TicketType.grants_membership == True)).all()
    return [ map_user_with_secret_fields_membership_personalia(user, request) for user in users ]

@view_config(context=EventInstanceResource, name='ticket_availability', request_method='GET', renderer='json', permission='ticket_availability_get')
def get_ticket_availability(context, request):
    event = context.eventInstance

    # Only report availability for ticket types the requester is allowed to see
    visible_mappings = request.db.query(EventTicketTypeMapping.uuid) \
        .filter(EventTicketTypeMapping.event_uuid == event.uuid)
    if request.authenticated_userid is None:
        visible_mappings = visible_mappings.filter(EventTicketTypeMapping.access_code == None)
    else:
        visible_mappings = visible_mappings.filter(or_(
            EventTicketTypeMapping.access_code == None,
            EventTicketTypeMapping.uuid.in_(
                select(EventTicketTypeMappingActivations.c.event_ticket_type_mapping_uuid) \
                    .where(EventTicketTypeMappingActivations.c.user_uuid == request.authenticated_userid)
            )
        ))
    visible_mapping_uuids = set(row[0] for row in visible_mappings.all())

    # Precalc the sales by ticket type, as the two next functions depend on it
    ticket_type_sales = event.get_sales_by_ticket_type(request.db)

    group_availability = event.get_ticket_group_availability(request.db, ticket_type_sales)
    ticket_type_availability = event.get_ticket_type_availability(request.db, ticket_type_sales, group_availability)

    return {
        'ticket_types': [ entry for entry in ticket_type_availability if entry['ticket_type_mapping_uuid'] in visible_mapping_uuids ],
        'groups': [ { 'group': group, 'remaining': remaining } for group, remaining in group_availability.items() ]
    }

@view_config(context=EventInstanceResource, name='ticket_type_mapping', request_method='GET', renderer='json', permission='ticket_type_mapping_list')
def get_ticket_type_mappings(context, request):
    return context.eventInstance.ticket_types

@view_config(context=EventInstanceResource, name='ticket_type_mapping', request_method='PUT', renderer='json', permission='ticket_type_mapping_create')
@validate(json_body={'ticket_type_uuid': str, 'sales_cap_groups': list})
def create_ticket_type_mapping(context, request):
    ticket_type = validateUuidAndQuery(request, TicketType, TicketType.uuid, request.json_body['ticket_type_uuid'])
    if ticket_type is None:
        request.response.status = 400
        return {
            'error': "Ticket type not found"
        }
    if ticket_type.event_brand_uuid != context.eventInstance.event_brand_uuid:
        request.response.status = 400
        return {
            'error': "Ticket type belongs to a different event brand"
        }

    error = list()

    sales_cap = request.json_body.get('sales_cap', None)
    if sales_cap is not None:
        if type(sales_cap) != int:
            error.append("Invalid type of sales_cap (not integer or null)")
        elif sales_cap < 0:
            error.append("sales_cap cannot be negative")

    sales_cap_groups = list()
    for group in request.json_body['sales_cap_groups']:
        if type(group) != str:
            error.append("Invalid type of sales_cap_groups entry (not string)")
            continue
        group = group.strip()
        if len(group) == 0:
            error.append("sales_cap_groups cannot contain an empty group name")
        elif group in sales_cap_groups:
            error.append("sales_cap_groups contains %s more than once" % group)
        else:
            sales_cap_groups.append(group)

    # A mapping for a ticket type that grants admission must be limited by something, or we could admit an unlimited
    # amount of people. Other ticket types may be sold without limit
    if ticket_type.grants_admission and sales_cap is None and len(request.json_body['sales_cap_groups']) == 0:
        error.append("A ticket type mapping relating to a ticket type that grants admission must either have a sales_cap or belong to at least one sales cap group")

    generate_code = request.json_body.get('generate_code', False)
    if type(generate_code) != bool:
        error.append("Invalid type of generate_code (not boolean)")

    if len(error) > 0:
        request.response.status = 400
        return {
            'error': ",".join(error)
        }

    existing_mapping = request.db.query(EventTicketTypeMapping) \
        .filter(and_(
            EventTicketTypeMapping.event_uuid == context.eventInstance.uuid,
            EventTicketTypeMapping.ticket_type_uuid == ticket_type.uuid
        )) \
        .first()
    if existing_mapping is not None:
        request.response.status = 400
        return {
            'error': "The ticket type is already mapped to this event"
        }

    mapping = EventTicketTypeMapping(context.eventInstance, ticket_type, sales_cap_groups, generate_code, sales_cap)
    request.db.add(mapping)
    request.db.flush()
    return mapping

@view_config(context=EventInstanceResource, name='unlock_ticket_type', request_method='POST', renderer='json', permission='unlock_ticket_type')
@validate(json_body={'code': str})
def unlock_ticket_type(context, request):
    code = request.json_body['code'].strip()
    if len(code) == 0:
        request.response.status = 400
        return {
            'error': "code cannot be empty"
        }

    mapping = request.db.query(EventTicketTypeMapping) \
        .filter(and_(
            EventTicketTypeMapping.event_uuid == context.eventInstance.uuid,
            EventTicketTypeMapping.access_code == code
        )) \
        .first()
    if mapping is None:
        return {
            'success': False
        }

    if mapping not in request.user.event_ticket_type_activations:
        request.user.event_ticket_type_activations.append(mapping)
    return {
        'success': True
    }

@view_config(context=EventInstanceResource, name='ticketType', request_method='GET', renderer='json', permission='event_ticket_type_get')
def get_ticket_types(context, request):
    # Ticket types with an access code are only shown to users who have unlocked them
    mappings = request.db.query(EventTicketTypeMapping) \
        .filter(EventTicketTypeMapping.event_uuid == context.eventInstance.uuid)
    if request.authenticated_userid is None:
        mappings = mappings.filter(EventTicketTypeMapping.access_code == None)
    else:
        mappings = mappings.filter(or_(
            EventTicketTypeMapping.access_code == None,
            EventTicketTypeMapping.uuid.in_(
                select(EventTicketTypeMappingActivations.c.event_ticket_type_mapping_uuid) \
                    .where(EventTicketTypeMappingActivations.c.user_uuid == request.authenticated_userid)
            )
        ))
    return [ mapping.ticket_type for mapping in mappings.order_by(EventTicketTypeMapping.created).all() ]

# Get all card orders for specified or current event
@view_config(name="card_orders", context=EventInstanceResource, request_method="GET", renderer="json", permission="list_card_orders")
def get_card_orders(context, request):
    # We either get the specified event or the current event
    return request.db.query(CardOrder).filter(CardOrder.event == context.eventInstance).all()

# Generates the crew card a given user gets for this event
@view_config(name='crew_card', context=EventInstanceResource, request_method='GET', renderer='pillow', permission='get_crew_card')
@validate(get=['user_uuid'])
def create_crew_card(context, request):
    # The pillow renderer can only render images, so errors have to be raised
    user = validateUuidAndQuery(request, User, User.uuid, request.GET['user_uuid'])
    if user is None:
        raise HTTPBadRequest("User not found")

    # A crew card only makes sense for someone holding a position at the event.
    # Lifetime positions count, the same way generate_badge treats them, but only
    # when they are global or belong to the brand putting on the event
    mapping = request.db.query(PositionMapping) \
        .join(Position) \
        .filter(and_(
            PositionMapping.user == user,
            or_(
                PositionMapping.event == context.eventInstance,
                and_(
                    PositionMapping.event == None,
                    or_(
                        Position.event_brand_uuid == None,
                        Position.event_brand_uuid == context.eventInstance.event_brand_uuid
                    )
                )
            )
        )) \
        .first()
    if mapping is None:
        raise HTTPBadRequest("User does not belong to this event")

    return generate_badge(request, user, context.eventInstance)

@view_config(name='', context=EventInstanceResource, request_method='PATCH', renderer='json', permission='event_edit')
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

    update_ticket_sales_caps = False
    if 'ticket_sales_caps' in request.json_body:
        ticket_sales_caps_error = validate_ticket_sales_caps(request.json_body['ticket_sales_caps'])
        if ticket_sales_caps_error is not None:
            error.append("Failed to update ticket_sales_caps, %s" % ticket_sales_caps_error)
        update_ticket_sales_caps = True

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
    
    if update_ticket_sales_caps is True:
        context.eventInstance.ticket_sales_caps = request.json_body['ticket_sales_caps']
    
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
