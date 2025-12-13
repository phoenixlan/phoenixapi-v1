from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPBadRequest,
    HTTPNotFound,
    HTTPInternalServerError
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow


from phoenixRest.models.tickets.payment import Payment, PaymentProvider
from phoenixRest.models.tickets.store_session import StoreSession
from phoenixRest.models.core.event import get_current_event

from phoenixRest.utils import validate
from phoenixRest.resource import resource

from phoenixRest.roles import ADMIN, TICKET_ADMIN

from phoenixRest.views.payment.instance import PaymentInstanceResource

from datetime import datetime

import logging
log = logging.getLogger(__name__)

@resource(name='payment')
class PaymentResource(object):
    __acl__ = [
        (Allow, Authenticated, 'create'),
        (Allow, ADMIN, 'fetch_all'),
        (Allow, TICKET_ADMIN, 'fetch_all'),

        # Authenticated pages
        #(Allow, Authenticated, Authenticated),
        #(Deny, Everyone, Authenticated),
    ]

    def __getitem__(self, key):
        """Traverse to a specific payment"""
        node = PaymentInstanceResource(self.request, key)
        node.__parent__ = self
        node.__name__ = key
        return node

    def __init__(self, request):
        self.request = request


@view_config(context=PaymentResource, name='', request_method='GET', renderer='json', permission='fetch_all')
def get_all_payments(request):
    # Returns all payments
    return request.db.query(Payment).order_by(Payment.created).all()

@view_config(context=PaymentResource, name='', request_method='POST', renderer='json', permission='create')
@validate(json_body={'store_session': str, 'provider': str})
def create_payment(context, request):
    # Validate provider
    chosen_provider = PaymentProvider[request.json_body['provider']]
    if chosen_provider is None:
        request.response.status = 400
        return {
            "error": "Invalid payment provider"
        }
    
    # Store session
    store_session = request.db.query(StoreSession).filter(StoreSession.uuid == request.json_body['store_session']).first()

    if not store_session or store_session.user != request.user:
        request.response.status = 404
        return {
            "error": "Store session not found"
        }
    
    if datetime.now() > store_session.expires:
        request.response.status = 400
        return {
            "error": "The store session has expired. Please create a new order"
        }
    
    # Make sure you can't create two payments for the same store session
    existing_payment = request.db.query(Payment).filter(Payment.store_session == store_session).first()
    if existing_payment:
        request.response.status = 400
        return {
            "error": "You have already created a payment for this card. Please finish it!"
        }

    payment = Payment(request.user, chosen_provider, store_session.get_total(), store_session.event)
    payment.store_session = store_session

    request.db.add(payment)
    request.db.flush()

    return payment
