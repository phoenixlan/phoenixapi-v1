from operator import and_
from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPNotFound,
    HTTPBadRequest
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow

from phoenixRest.models import db
from phoenixRest.models.core.user import User
from phoenixRest.models.tickets.ticket_transfer import TicketTransfer
from phoenixRest.models.tickets.row import Row

from phoenixRest.roles import ADMIN, TICKET_ADMIN

from phoenixRest.utils import validate, validateUuidAndQuery
from phoenixRest.resource import resource

from sqlalchemy import and_

from datetime import datetime, timedelta

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

        self.ticketTransferInstance = validateUuidAndQuery(TicketTransfer, TicketTransfer.uuid, uuid)

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





