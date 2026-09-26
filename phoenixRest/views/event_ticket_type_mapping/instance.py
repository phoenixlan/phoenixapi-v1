from pyramid.view import view_config
from pyramid.httpexceptions import (
    HTTPNotFound
)
from pyramid.authorization import Allow

from phoenixRest.models.core.event_ticket_type_mapping import EventTicketTypeMapping
from phoenixRest.models.core.user import EventTicketTypeMappingActivations
from phoenixRest.models.tickets.ticket import Ticket
from phoenixRest.models.tickets.store_session import StoreSession
from phoenixRest.models.tickets.store_session_cart_entry import StoreSessionCartEntry

from phoenixRest.roles import ADMIN, BRAND_ADMIN, TICKET_ADMIN

from phoenixRest.utils import validateUuidAndQuery

from sqlalchemy import and_

from datetime import datetime

import logging
log = logging.getLogger(__name__)


class EventTicketTypeMappingInstanceResource(object):
    def __acl__(self):
        event_brand_uuid = self.eventTicketTypeMappingInstance.event.event_brand_uuid
        return [
            (Allow, ADMIN(), 'delete'),
            (Allow, BRAND_ADMIN(event_brand_uuid), 'delete'),
            (Allow, TICKET_ADMIN(event_brand_uuid), 'delete'),

            (Allow, ADMIN(), 'rotate'),
            (Allow, BRAND_ADMIN(event_brand_uuid), 'rotate'),
            (Allow, TICKET_ADMIN(event_brand_uuid), 'rotate'),
        ]

    def __init__(self, request, uuid):
        self.request = request
        self.eventTicketTypeMappingInstance = validateUuidAndQuery(request, EventTicketTypeMapping, EventTicketTypeMapping.uuid, uuid)

        if self.eventTicketTypeMappingInstance is None:
            raise HTTPNotFound("Event ticket type mapping not found")

@view_config(context=EventTicketTypeMappingInstanceResource, name='', request_method='DELETE', renderer='json', permission='delete')
def delete_event_ticket_type_mapping(context, request):
    mapping = context.eventTicketTypeMappingInstance

    # Sold tickets only count towards sales cap groups through their mapping, so removing
    # the mapping would free up their spots and let us sell more tickets than we have
    sold_tickets = request.db.query(Ticket) \
        .filter(and_(
            Ticket.event_uuid == mapping.event_uuid,
            Ticket.ticket_type_uuid == mapping.ticket_type_uuid
        )) \
        .count()
    if sold_tickets > 0:
        request.response.status = 400
        return {
            'error': "Tickets of this type have already been sold for the event"
        }

    reserved_tickets = request.db.query(StoreSessionCartEntry) \
        .join(StoreSession, StoreSession.uuid == StoreSessionCartEntry.store_session_uuid) \
        .filter(and_(
            StoreSession.event_uuid == mapping.event_uuid,
            StoreSession.expires > datetime.now(),
            StoreSessionCartEntry.ticket_type_uuid == mapping.ticket_type_uuid
        )) \
        .count()
    if reserved_tickets > 0:
        request.response.status = 400
        return {
            'error': "Tickets of this type are currently reserved by someone buying them"
        }

    log.info("Deleting ticket type mapping %s for ticket type %s on event %s" % (mapping.uuid, mapping.ticket_type_uuid, mapping.event_uuid))

    # Users who unlocked the ticket type reference the mapping
    request.db.execute(
        EventTicketTypeMappingActivations.delete() \
            .where(EventTicketTypeMappingActivations.c.event_ticket_type_mapping_uuid == mapping.uuid)
    )
    request.db.delete(mapping)

    return {
        'success': True
    }

@view_config(context=EventTicketTypeMappingInstanceResource, name='rotate', request_method='POST', renderer='json', permission='rotate')
def rotate_event_ticket_type_mapping_access_code(context, request):
    mapping = context.eventTicketTypeMappingInstance

    if mapping.access_code is None:
        request.response.status = 400
        return {
            'error': "The ticket type mapping has no access code to rotate"
        }

    # Users who already unlocked the ticket type keep access. Only the old code stops working
    log.info("Rotating access code of ticket type mapping %s" % mapping.uuid)
    mapping.access_code = EventTicketTypeMapping.get_access_code()
    request.db.flush()

    return mapping
