from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPNotFound,
    HTTPBadRequest
)
from pyramid.security import Authenticated, Everyone, Deny, Allow

from phoenixRest.models import db
from phoenixRest.models.core.event import Event
from phoenixRest.models.tickets.ticket import Ticket
from phoenixRest.models.tickets.row import Row
from phoenixRest.models.tickets.seatmap import Seatmap
from phoenixRest.models.tickets.ticket_type import TicketType

from phoenixRest.mappers.crew import map_crew

from phoenixRest.roles import ADMIN, EVENT_ADMIN, CHIEF, TICKET_ADMIN

from phoenixRest.utils import validate
from phoenixRest.resource import resource

from datetime import datetime
import os

import logging
log = logging.getLogger(__name__)

from PIL import Image

class EventInstanceResource(object):
    def __acl__(self):
        acl = [
            (Allow, Everyone, 'event_get'),
            (Allow, ADMIN, 'event_get'),
            (Allow, EVENT_ADMIN, 'event_get'),

            (Allow, Everyone, 'event_ticket_type_get'),
            (Allow, ADMIN, 'event_ticket_type_get'),
            (Allow, EVENT_ADMIN, 'event_ticket_type_get'),

            (Allow, ADMIN, 'event_tickets_get'),
            (Allow, TICKET_ADMIN, 'event_tickets_get'),

            (Allow, CHIEF, 'applications_get'),
            (Allow, ADMIN, 'applications_get'),
        ]
        return acl

    def __init__(self, request, uuid):
        self.request = request
        self.eventInstance = db.query(Event).filter(Event.uuid == uuid).first()

        if self.eventInstance is None:
            raise HTTPNotFound("Event not found")

@view_config(context=EventInstanceResource, name='', request_method='GET', renderer='json', permission='event_get')
def get_event(context, request):
    return context.eventInstance

# Objects relating to the specific event
@view_config(context=EventInstanceResource, name='applications', request_method='GET', renderer='json', permission='applications_get')
def get_applications(context, request):
    applications = db.query(Application).filter(Application.event_uuid == context.eventInstance.uuid).order_by(Application.created.asc()).all()
    return applications

@view_config(context=EventInstanceResource, name='ticket', request_method='GET', renderer='json', permission='event_tickets_get')
def get_tickets(context, request):
    tickets = db.query(Ticket).filter(Ticket.event_uuid == context.eventInstance.uuid).all()
    return tickets

@view_config(context=EventInstanceResource, name='ticketType', request_method='GET', renderer='json', permission='event_ticket_type_get')
def get_ticket_types(context, request):
    # Ticket types deduced through rows configured to only allow them
    row_types = db.query(TicketType) \
        .join(Row, TicketType.uuid == Row.ticket_type_uuid) \
        .join(Seatmap, Row.seatmap_uuid == Seatmap.uuid) \
        .join(Event, Event.seatmap_uuid == Seatmap.uuid) \
        .filter(Event.uuid == context.eventInstance.uuid).all()

    # Ticket types assigned to the event
    static_types = context.eventInstance.static_ticket_types
    return list(set(row_types+static_types))
