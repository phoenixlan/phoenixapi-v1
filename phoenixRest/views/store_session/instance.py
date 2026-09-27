from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotFound
from pyramid.authorization import Allow

from phoenixRest.models.tickets.payment import Payment, PaymentProvider
from phoenixRest.models.tickets.store_session import StoreSession

from phoenixRest.utils import validate, validateUuidAndQuery

from datetime import datetime

import logging
log = logging.getLogger(__name__)


class StoreSessionInstanceResource(object):
    def __acl__(self):
        return [
            # Everyone may create a payment for their own store session
            (Allow, 'role:user:%s' % self.storeSessionInstance.user.uuid, 'create_payment')
        ]

    def __init__(self, request, uuid):
        self.request = request
        self.storeSessionInstance = validateUuidAndQuery(request, StoreSession, StoreSession.uuid, uuid)

        if self.storeSessionInstance is None:
            raise HTTPNotFound("Store session not found")

@view_config(context=StoreSessionInstanceResource, name='payment', request_method='POST', renderer='json', permission='create_payment')
@validate(json_body={'provider': str})
def create_payment(context, request):
    store_session = context.storeSessionInstance

    # Validate provider
    try:
        chosen_provider = PaymentProvider[request.json_body['provider']]
    except KeyError:
        request.response.status = 400
        return {
            "error": "Invalid payment provider"
        }

    if chosen_provider == PaymentProvider.vipps and 'vipps' not in request.feature_flags:
        request.response.status = 400
        return {
            "error": "Vipps payments are not enabled"
        }

    if chosen_provider == PaymentProvider.stripe and 'stripe' not in request.feature_flags:
        request.response.status = 400
        return {
            "error": "Stripe payments are not enabled"
        }

    if chosen_provider == PaymentProvider.free and store_session.get_total() > 0:
        log.error("User %s (%s) tried to get non-free tickets for free: %s" % (
            request.user.uuid,
            request.user.email,
            ", ".join(entry.ticket_type.name for entry in store_session.cart_entries)
        ))
        request.response.status = 400
        return {
            "error": "This cart is not free"
        }

    if datetime.now() > store_session.expires:
        request.response.status = 400
        return {
            "error": "The store session has expired. Please create a new order"
        }

    if request.user.membership_personalia is None and \
            any(entry.ticket_type.grants_membership for entry in store_session.cart_entries):
        request.response.status = 400
        return {
            "error": "You must fill in your membership personalia before buying a ticket that grants membership"
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
