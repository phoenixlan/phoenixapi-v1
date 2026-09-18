from datetime import datetime

from pyramid.authorization import Allow, Authenticated
from pyramid.view import view_config

from phoenixRest.models.core.event import get_current_events
from phoenixRest.models.tickets.store_session import StoreSession
from phoenixRest.models.tickets.store_session_cart_entry import StoreSessionCartEntry
from phoenixRest.models.tickets.ticket_type import TicketType
from phoenixRest.roles import (
    ADMIN,
    TICKET_BYPASS_TICKETSALE_START_RESTRICTION,
    TICKET_WHOLESALE
)
from phoenixRest.utils import validate


class EventStoreSessionResource(object):
    __acl__ = [
        (Allow, Authenticated, 'create')
    ]

    def __init__(self, request, event):
        self.request = request
        self.event = event


@view_config(context=EventStoreSessionResource, request_method='PUT', renderer='json', permission='create')
@validate(json_body={'cart': list})
def create_store_session(context, request):
    max_purchase_amt = int(request.registry.settings['ticket.max_purchase_amt'])
    store_session_lifetime = int(request.registry.settings['ticket.store_session_lifetime'])
    event = context.event

    active_events = list(map(lambda u: str(u), get_current_events(request.db)))
    if str(event.uuid) not in active_events:
        request.response.status = 400
        return {
            "error": "Event is not current - you can't create a store session for a non-curent event"
        }

    if datetime.now() < event.booking_time and \
            ADMIN() not in request.effective_principals and \
            TICKET_BYPASS_TICKETSALE_START_RESTRICTION(event.event_brand_uuid) not in request.effective_principals:
        request.response.status = 400
        return {
            'error': "The ticket sale hasn't started yet"
        }

    if len(request.json_body['cart']) == 0:
        request.response.status = 400
        return {
            "error": "The cart is empty"
        }

    store_session = StoreSession(request.user, store_session_lifetime, event)

    total_qty = 0
    for entry in request.json_body['cart']:
        if 'uuid' not in entry:
            request.response.status = 400
            return {
                "error": "Cart entry lacks uuid"
            }
        if 'qty' not in entry:
            request.response.status = 400
            return {
                "error": "Cart entry lacks qtr"
            }
        if type(entry['qty']) != int:
            request.response.status = 400
            return {
                "error": "Quantity is not a number"
            }
        if entry['qty'] < 0:
            request.response.status = 400
            return {
                "error": "Quantity is negative"
            }
        if entry['qty'] == 0:
            continue

        total_qty += entry['qty']

        ticket_type = request.db.query(TicketType) \
            .filter(TicketType.uuid == entry['uuid']) \
            .first()
        if ticket_type is None:
            request.response.status = 400
            return {
                "error": "Ticket type not found"
            }
        if ticket_type.event_brand_uuid is not None and \
                ticket_type.event_brand_uuid != event.event_brand_uuid:
            request.response.status = 400
            return {
                "error": "Ticket type belongs to a different event brand"
            }

        store_session.cart_entries.append(
            StoreSessionCartEntry(ticket_type, entry['qty'])
        )

    if total_qty > max_purchase_amt and \
            ADMIN() not in request.effective_principals and \
            TICKET_WHOLESALE(event.event_brand_uuid) not in request.effective_principals:
        request.response.status = 400
        return {
            "error": "You can only buy %s tickets at a time" % max_purchase_amt
        }

    if total_qty > event.get_total_ticket_availability(request):
        request.response.status = 400
        return {
            "error": "There aren't that many tickets available(There are only %s tickets available)" % (
                event.get_total_ticket_availability(request)
            )
        }

    request.db.add(store_session)
    request.db.flush()
    return store_session
