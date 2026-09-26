from datetime import datetime

from pyramid.authorization import Allow, Authenticated
from pyramid.view import view_config

from sqlalchemy import and_, or_, select

from phoenixRest.models.core.event import Event, get_current_events
from phoenixRest.models.core.event_ticket_type_mapping import EventTicketTypeMapping
from phoenixRest.models.core.user import EventTicketTypeMappingActivations
from phoenixRest.models.tickets.store_session import StoreSession
from phoenixRest.models.tickets.store_session_cart_entry import StoreSessionCartEntry
from phoenixRest.models.tickets.ticket_type import TicketType
from phoenixRest.roles import (
    ADMIN,
    TICKET_BYPASS_TICKETSALE_START_RESTRICTION,
    TICKET_WHOLESALE
)
from phoenixRest.utils import validate, validateUuidAndQuery

import logging
log = logging.getLogger(__name__)


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

    # Lock the event so concurrent purchases can't both reserve the last tickets
    event = request.db.query(Event) \
        .filter(Event.uuid == context.event.uuid) \
        .with_for_update() \
        .one()

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

    # Ticket types with an access code can only be bought by users who have unlocked them
    visible_ticket_type_uuids = set(row[0] for row in request.db.query(EventTicketTypeMapping.ticket_type_uuid) \
        .filter(and_(
            EventTicketTypeMapping.event_uuid == event.uuid,
            or_(
                EventTicketTypeMapping.access_code == None,
                EventTicketTypeMapping.uuid.in_(
                    select(EventTicketTypeMappingActivations.c.event_ticket_type_mapping_uuid) \
                        .where(EventTicketTypeMappingActivations.c.user_uuid == request.user.uuid)
                )
            )
        )) \
        .all())

    # Ticket type uuid -> quantity. Entries with the same ticket type are merged
    cart = dict()
    ticket_types = dict()
    for entry in request.json_body['cart']:
        if type(entry) != dict:
            request.response.status = 400
            return {
                "error": "Cart entry is not an object"
            }
        if 'uuid' not in entry:
            request.response.status = 400
            return {
                "error": "Cart entry lacks uuid"
            }
        if 'qty' not in entry:
            request.response.status = 400
            return {
                "error": "Cart entry lacks qty"
            }
        if type(entry['uuid']) != str:
            request.response.status = 400
            return {
                "error": "Cart entry uuid is not a string"
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

        ticket_type = validateUuidAndQuery(request, TicketType, TicketType.uuid, entry['uuid'])
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
        if ticket_type.uuid not in visible_ticket_type_uuids:
            request.response.status = 400
            return {
                "error": "Ticket type is not available for this event"
            }

        ticket_types[ticket_type.uuid] = ticket_type
        cart[ticket_type.uuid] = cart.get(ticket_type.uuid, 0) + entry['qty']

    if len(cart) == 0:
        request.response.status = 400
        return {
            "error": "The cart is empty"
        }

    total_qty = sum(cart.values())
    if total_qty > max_purchase_amt and \
            ADMIN() not in request.effective_principals and \
            TICKET_WHOLESALE(event.event_brand_uuid) not in request.effective_principals:
        request.response.status = 400
        return {
            "error": "You can only buy %s tickets at a time" % max_purchase_amt
        }

    # An admission ticket type that no cap applies to could be sold without limit. This should be impossible
    # to configure through the API, so it is our fault if it happens
    for mapping in event.ticket_types:
        if mapping.ticket_type_uuid in cart and \
                mapping.ticket_type.grants_admission and \
                mapping.sales_cap is None and \
                len(mapping.sales_cap_groups) == 0:
            log.error("Ticket type mapping %s grants admission, but has no sales cap and belongs to no sales cap group" % mapping.uuid)
            request.response.status = 500
            return {
                "error": "Sorry! We configured it wrong"
            }

    # Precalc the sales by ticket type, as the two next functions depend on it
    ticket_type_sales = event.get_sales_by_ticket_type(request.db)

    group_availability = event.get_ticket_group_availability(request.db, ticket_type_sales)
    ticket_type_availability = event.get_ticket_type_availability(request.db, ticket_type_sales, group_availability)

    for entry in ticket_type_availability:
        qty = cart.get(entry['ticket_type'].uuid, 0)
        if entry['remaining'] is not None and qty > entry['remaining']:
            request.response.status = 400
            return {
                "error": "There aren't that many %s tickets available" % entry['ticket_type'].name
            }

    # Ticket types that are individually available may still together exceed a group they share
    for group, remaining in group_availability.items():
        group_qty = sum(
            cart.get(entry['ticket_type'].uuid, 0) for entry in ticket_type_availability
            if group in entry['groups']
        )
        if group_qty > remaining:
            request.response.status = 400
            return {
                "error": "There aren't that many tickets available"
            }

    store_session = StoreSession(request.user, store_session_lifetime, event)
    for ticket_type_uuid, qty in cart.items():
        store_session.cart_entries.append(
            StoreSessionCartEntry(ticket_types[ticket_type_uuid], qty)
        )

    request.db.add(store_session)
    request.db.flush()
    return store_session
