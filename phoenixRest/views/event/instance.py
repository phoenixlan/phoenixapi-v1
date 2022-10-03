from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPNotFound,
    HTTPBadRequest
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow

from phoenixRest.models.core.event import Event
from phoenixRest.models.core.user import User
from phoenixRest.models.tickets.ticket import Ticket
from phoenixRest.models.tickets.row import Row
from phoenixRest.models.tickets.seatmap import Seatmap
from phoenixRest.models.tickets.ticket_type import TicketType

from phoenixRest.mappers.user import map_user_simple_with_secret_fields

from phoenixRest.roles import ADMIN, EVENT_ADMIN, CHIEF, HR_ADMIN, TICKET_ADMIN, TICKET_CHECKIN

from phoenixRest.utils import validate

from sqlalchemy import and_

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
def get_applications(context, request):
    applications = request.db.query(Application).filter(Application.event_uuid == context.eventInstance.uuid).order_by(Application.created.asc()).all()
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
