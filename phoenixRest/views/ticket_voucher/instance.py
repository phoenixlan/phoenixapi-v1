from operator import and_
from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPNotFound,
    HTTPBadRequest
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow

from phoenixRest.models.tickets.ticket_voucher import TicketVoucher
from phoenixRest.models.tickets.ticket import Ticket
from phoenixRest.models.core.event import get_current_event

from phoenixRest.roles import ADMIN, TICKET_ADMIN

from phoenixRest.utils import validateUuidAndQuery

from datetime import datetime

import logging
log = logging.getLogger(__name__)

class TicketVoucherInstanceResource(object):
    def __acl__(self):
        acl = [
            (Allow, ADMIN, 'burn'),
            (Allow, TICKET_ADMIN, 'burn'),
            # Authenticated pages
            #(Allow, Authenticated, Authenticated),
            #(Deny, Everyone, Authenticated),
        ]
        if self.request.user is not None:
            acl = acl + [
                # The person that initiated a ticket transfer may revert it
                (Allow, "%s" % self.ticketVoucherInstance.recipient_user.uuid, 'burn'),
            ]
        return acl

    def __init__(self, request, uuid):
        self.request = request

        self.ticketVoucherInstance = validateUuidAndQuery(request, TicketVoucher, TicketVoucher.uuid, uuid)

        if self.ticketVoucherInstance is None:
            raise HTTPNotFound("Ticket voucher not found")

@view_config(context=TicketVoucherInstanceResource, name='burn', request_method='POST', renderer='json', permission='burn')
def burn_voucher(context, request):
    if context.ticketVoucherInstance.used is not None:
        request.response.status = 400
        return {
            'error': "The voucher has already been used"
        }
    
    if context.ticketVoucherInstance.is_expired():
        request.response.status = 400
        return {
            'error': "The has expired - contact support"
        }

    # Mint the ticket!
    context.ticketVoucherInstance.used = datetime.now()
    ticket = Ticket(context.ticketVoucherInstance.recipient_user, None, context.ticketVoucherInstance.ticket_type, get_current_event(request.db, context.ticketVoucherInstance.event_brand))
    context.ticketVoucherInstance.ticket = ticket

    # Save it
    request.db.add(ticket)
    request.db.flush()
    log.info(f"Minted ticket {ticket.ticket_id} by burning voucher {context.ticketVoucherInstance.uuid} for user {context.ticketVoucherInstance.recipient_user.uuid}")

    request.service_manager.get_service('email').send_mail(context.ticketVoucherInstance.recipient_user.email, "Du har brukt et billett-gavekort", "ticket_voucher_burned.jinja2", {
        "mail": request.registry.settings["api.contact"],
        "name": request.registry.settings["api.name"],
        "domain": request.registry.settings["api.mainpage"],
        "ticket_voucher": context.ticketVoucherInstance
    })
    return context.ticketVoucherInstance
