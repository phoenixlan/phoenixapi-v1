from pyramid.authorization import Allow
from pyramid.view import view_config

from phoenixRest.models.core.event import get_current_events
from phoenixRest.models.core.user import User
from phoenixRest.models.tickets.ticket import Ticket
from phoenixRest.models.tickets.ticket_type import TicketType
from phoenixRest.roles import ADMIN, TICKET_ADMIN, TICKET_CHECKIN
from phoenixRest.utils import validate


class EventTicketResource(object):
    def __acl__(self):
        return [
            (Allow, ADMIN(), 'create'),
            (Allow, TICKET_ADMIN(self.event.event_brand_uuid), 'create'),
            (Allow, ADMIN(), 'get'),
            (Allow, TICKET_ADMIN(self.event.event_brand_uuid), 'get'),
            (Allow, TICKET_CHECKIN(self.event.event_brand_uuid), 'get')
        ]

    def __init__(self, request, event):
        self.request = request
        self.event = event


@view_config(context=EventTicketResource, request_method='GET', renderer='json', permission='get')
def get_tickets(context, request):
    return request.db.query(Ticket) \
        .filter(Ticket.event_uuid == context.event.uuid) \
        .order_by(Ticket.ticket_id) \
        .all()


@view_config(context=EventTicketResource, request_method='POST', renderer='json', permission='create')
@validate(json_body={'recipient': str, 'ticket_type': str})
def create_ticket(context, request):
    receiving_user = request.db.query(User) \
        .filter(User.uuid == request.json_body['recipient']) \
        .first()
    if not receiving_user:
        request.response.status = 400
        return {
            "error": "Recipient user not found"
        }

    ticket_type = request.db.query(TicketType) \
        .filter(TicketType.uuid == request.json_body['ticket_type']) \
        .first()
    if ticket_type is None:
        request.response.status = 400
        return {
            "error": "Ticket type not found"
        }
    if ticket_type.event_brand_uuid is not None and \
            ticket_type.event_brand_uuid != context.event.event_brand_uuid:
        request.response.status = 400
        return {
            "error": "Ticket type belongs to a different event brand"
        }

    active_events = list(map(lambda u: str(u), get_current_events(request.db)))
    if str(context.event.uuid) not in active_events:
        request.response.status = 400
        return {
            "error": "Event is not current - you can't create a ticket for a non-curent event"
        }

    ticket = Ticket(receiving_user, None, ticket_type, context.event)
    request.db.add(ticket)
    request.db.flush()

    request.service_manager.get_service('email').send_mail(
        receiving_user.email,
        "Du har mottatt en billett",
        "ticket_received.jinja2",
        {
            "mail": request.registry.settings['api.contact'],
            "domain": request.registry.settings['api.mainpage'],
            "type": ticket_type.name,
            "name": request.registry.settings['api.name'],
        }
    )
    return ticket
