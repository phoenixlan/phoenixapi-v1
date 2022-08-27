from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPBadRequest
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow


from phoenixRest.models import db
from phoenixRest.models.core.event import get_current_event
from phoenixRest.models.crew.crew import Crew
from phoenixRest.models.tickets.store_session import StoreSession
from phoenixRest.models.tickets.store_session_cart_entry import StoreSessionCartEntry
from phoenixRest.models.tickets.ticket_type import TicketType

from phoenixRest.utils import validate
from phoenixRest.resource import resource

from phoenixRest.roles import ADMIN, TICKET_BYPASS_TICKETSALE_START_RESTRICTION, TICKET_WHOLESALE, TICKET_ADMIN

from phoenixRest.views.crew.instance import CrewInstanceViews

from datetime import datetime

import logging
log = logging.getLogger(__name__)

@resource(name='store_session')
class StoreSessionResource(object):
    __acl__ = [
        (Allow, Authenticated, 'create'),
        (Allow, ADMIN, 'fetch_all'),
        (Allow, TICKET_ADMIN, 'fetch_all'),

        # Authenticated pages
        #(Allow, Authenticated, Authenticated),
        #(Deny, Everyone, Authenticated),
    ]
    def __init__(self, request):
        self.request = request


@view_config(context=StoreSessionResource, name='', request_method='GET', renderer='json', permission='fetch_all')
def get_all_sessions(request):
    # Returns all active store sessions
    return db.query(StoreSession).order_by(StoreSession.created).all()

@view_config(context=StoreSessionResource, name='', request_method='PUT', renderer='json', permission='create')
def create_store_session(context, request):
    max_purchase_amt = int(request.registry.settings["ticket.max_purchase_amt"])
    store_session_lifetime = int(request.registry.settings["ticket.store_session_lifetime"])
    event = get_current_event()

    if datetime.now() < event.booking_time and TICKET_BYPASS_TICKETSALE_START_RESTRICTION not in request.effective_principals:
        request.response.status = 400
        return {
            'error': "The ticket sale hasn't started yet"
        }

    if 'cart' not in request.json_body:
        request.response.status = 400
        return {
            "error": "Lacking json parameter: card"
        }
    if not isinstance(request.json_body['cart'], list):
        request.response.status = 400
        return {
            "error": "The card should be an array"
        }
    
    if len(request.json_body['cart']) == 0:
        request.response.status = 400
        return {
            "error": "The cart is empty"
        }

    # Expiry is prolonged when the user is sent to external payment, as some payment providers implement their own mechanism for this(vipps)
    store_session = StoreSession(request.user, store_session_lifetime)

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
        if  type(entry['qty']) != int:
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

        ticket_type = db.query(TicketType).filter(TicketType.uuid == entry['uuid']).first()
        if ticket_type is None:
            request.response.status = 400
            return {
                "error": "Ticket type not found"
            }

        store_session.cart_entries.append(StoreSessionCartEntry(ticket_type, entry['qty']))
    if total_qty > int(max_purchase_amt) and not TICKET_WHOLESALE in request.effective_principals:
        request.response.status = 400
        return {
            "error": "You can only buy %s tickets at a time" % max_purchase_amt
        }
    
    if total_qty > event.get_total_ticket_availability():
        request.response.status = 400
        return {
            "error": "There aren't that many tickets available(There are only %s tickets available)" % (event.get_total_ticket_availability())
        }

    db.add(store_session)
    db.flush()
    return store_session

