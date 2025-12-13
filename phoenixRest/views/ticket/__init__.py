from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPNotFound
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow


from phoenixRest.models.tickets.ticket_type import TicketType
from phoenixRest.models.core.user import User
from phoenixRest.models.core.event import Event
from phoenixRest.models.tickets.ticket import Ticket
from phoenixRest.models.core.event import get_current_events

from phoenixRest.utils import validate
from phoenixRest.resource import resource

from phoenixRest.roles import ADMIN, TICKET_ADMIN, TICKET_CHECKIN

from phoenixRest.views.ticket.instance import TicketInstanceResource

from datetime import datetime

import logging
log = logging.getLogger(__name__)

@resource(name='ticket')
class TicketResource(object):
    __acl__ = [
        (Allow, ADMIN, 'getAll'),
        (Allow, TICKET_ADMIN, 'getAll'),
        (Allow, TICKET_CHECKIN, 'getAll'),
        (Allow, ADMIN, 'create'),
        (Allow, TICKET_ADMIN, 'create'),

        # Authenticated pages
        #(Allow, Authenticated, Authenticated),
        #(Deny, Everyone, Authenticated),
    ]
    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        node = TicketInstanceResource(self.request, key)
        node.__parent__ = self
        node.__name__ = key
        return node

@view_config(name='', context=TicketResource, request_method='GET', renderer='json', permission='getAll')
def get_all_tickets(context, request):
    return request.db.query(Ticket).order_by(Ticket.ticket_id).all()

@view_config(name='', context=TicketResource, request_method='POST', renderer='json', permission='create')
@validate(json_body={'recipient': str, 'ticket_type': str, 'event_uuid': str})
def create_ticket(context, request):
    receiving_user = request.db.query(User).filter(User.uuid == request.json_body['recipient']).first()
    if not receiving_user:
        request.response.status = 400
        return {
            "error": "Recipient user not found"
        }

    ticket_type = request.db.query(TicketType).filter(TicketType.uuid == request.json_body['ticket_type']).first()
    if ticket_type is None:
        request.response.status = 400
        return {
            "error": "Ticket type not found"
        }

    event = request.db.query(Event).filter(Event.uuid == request.json_body["event_uuid"]).first()
    if event is None:
        request.response.status = 400
        return {
            "error": "Event not found"
        }

    active_events = list(map(lambda u: str(u), get_current_events(request.db)))
    if str(event.uuid) not in active_events:
        request.response.status = 400
        return {
            "error": f"Event is not current - you can't create a ticket for a non-curent event"
        }


    ticket = Ticket(receiving_user, None, ticket_type, event)
    request.db.add(ticket)
    request.db.flush()

    request.service_manager.get_service('email').send_mail(receiving_user.email, "Du har mottatt en billett", "ticket_received.jinja2", {
        "mail": request.registry.settings["api.contact"],
        "domain": request.registry.settings["api.mainpage"],
        "type": ticket_type.name,
        "name": request.registry.settings["api.name"],
    })
    return ticket

