from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow

from phoenixRest.models.core.user import User
from phoenixRest.models.core.event import Event
from phoenixRest.models.tickets.ticket_voucher import TicketVoucher
from phoenixRest.models.tickets.ticket_type import TicketType

from phoenixRest.views.ticket_voucher.instance import TicketVoucherInstanceResource

from phoenixRest.utils import validate
from phoenixRest.resource import resource

from phoenixRest.roles import ADMIN, TICKET_ADMIN

from sqlalchemy import and_, or_, extract

import logging
log = logging.getLogger(__name__)

@resource(name='ticket_voucher')
class TicketVoucherResource(object):
    __acl__ = [
        (Allow, ADMIN, 'create'),
        (Allow, TICKET_ADMIN, 'create'),

        (Allow, ADMIN, 'get'),
        (Allow, TICKET_ADMIN, 'get'),
    ]
    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        node = TicketVoucherInstanceResource(self.request, key)
        node.__parent__ = self
        node.__name__ = key
        return node

@view_config(name='', context=TicketVoucherResource, request_method='GET', renderer='json', permission='get')
def get_vouchers(context, request):
    return request.db.query(TicketVoucher).all()

@view_config(name='', context=TicketVoucherResource, request_method='POST', renderer='json', permission='create')
@validate(json_body={'recipient_user_uuid': str, 'ticket_type_uuid': str, 'last_use_event_uuid': str})
def create_voucher(context, request):
    recipient_user = request.db.query(User).filter(User.uuid == request.json_body['recipient_user_uuid']).first()
    if not recipient_user:
        request.response.status = 404
        return {
            "error": "recipient_user not found"
        }
    
    ticket_type = request.db.query(TicketType).filter(TicketType.uuid == request.json_body['ticket_type_uuid']).first()
    if not ticket_type:
        request.response.status = 404
        return {
            "error": "ticket_type not found"
        }

    last_use_event = request.db.query(Event).filter(Event.uuid == request.json_body['last_use_event_uuid']).first()
    if not last_use_event:
        request.response.status = 404
        return {
            "error": "last_use_event not found"
        }

    voucher = TicketVoucher(request.user, recipient_user, ticket_type, last_use_event)
    request.db.add(voucher)
    request.db.flush()

    request.service_manager.get_service('email').send_mail(recipient_user.email, "Du har mottatt et billett-gavekort", "ticket_voucher_received.jinja2", {
        "mail": request.registry.settings["api.contact"],
        "name": request.registry.settings["api.name"],
        "domain": request.registry.settings["api.mainpage"],
        "ticket_type": ticket_type,
        "last_use_event": last_use_event
    })

    return voucher


