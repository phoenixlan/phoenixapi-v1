from operator import and_
from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPNotFound,
    HTTPBadRequest
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow

from phoenixRest.models.tickets.ticket_transfer import TicketTransfer

from phoenixRest.roles import ADMIN, TICKET_ADMIN

from phoenixRest.utils import validateUuidAndQuery

import logging
log = logging.getLogger(__name__)

class TicketTransferInstanceResource(object):
    def __acl__(self):
        acl = [
            (Allow, ADMIN, 'revert'),
            (Allow, TICKET_ADMIN, 'revert'),
            # Authenticated pages
            #(Allow, Authenticated, Authenticated),
            #(Deny, Everyone, Authenticated),
        ]
        if self.request.user is not None:
            acl = acl + [
                # The person that initiated a ticket transfer may revert it
                (Allow, "%s" % self.ticketTransferInstance.from_user.uuid, 'revert'),
            ]

        return acl

    def __init__(self, request, uuid):
        self.request = request

        self.ticketTransferInstance = validateUuidAndQuery(request, TicketTransfer, TicketTransfer.uuid, uuid)

        if self.ticketTransferInstance is None:
            raise HTTPNotFound("Ticket transfer not found")

@view_config(context=TicketTransferInstanceResource, name='revert', request_method='POST', renderer='json', permission='revert')
def revert_transfer(context, request):
    if context.ticketTransferInstance.reverted:
        request.response.status = 400
        return {
            'error': "The transfer has already been reverted"
        }
    context.ticketTransferInstance.reverted = True
    context.ticketTransferInstance.ticket.owner = context.ticketTransferInstance.from_user

    request.service_manager.get_service('email').send_mail(context.ticketTransferInstance.from_user.email, "Du har angret på en billett-overføring", "ticket_transfer_reverted_to_sender.jinja2", {
        "mail": request.registry.settings["api.contact"],
        "name": request.registry.settings["api.name"],
        "domain": request.registry.settings["api.mainpage"],
        "ticket": context.ticketTransferInstance.ticket
    })

    request.service_manager.get_service('email').send_mail(context.ticketTransferInstance.to_user.email, "Senderen har angret på overføringen av en billett til deg", "ticket_transfer_reverted_to_recipient.jinja2", {
        "mail": request.registry.settings["api.contact"],
        "name": request.registry.settings["api.name"],
        "domain": request.registry.settings["api.mainpage"],
        "sender": request.user,
        "ticket": context.ticketTransferInstance.ticket
    })
    return {
        "status": "ok"
    }
