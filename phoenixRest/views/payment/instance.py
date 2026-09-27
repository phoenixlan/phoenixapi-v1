from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPBadRequest,
    HTTPNotFound
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow

from phoenixRest.models.tickets.payment import Payment, PaymentState, PaymentProvider

from phoenixRest.roles import ADMIN, TICKET_ADMIN

from phoenixRest.features.payment.vipps import initialize_vipps_payment
from phoenixRest.features.payment.stripe import initialize_stripe_payment
from phoenixRest.features.payment import mint_tickets

from sqlalchemy.orm import joinedload

from datetime import datetime

import logging
log = logging.getLogger(__name__)


class PaymentInstanceResource(object):
    def __acl__(self):
        return [
            (Allow, ADMIN(), 'get_payment'),
            (Allow, TICKET_ADMIN(self.paymentInstance.event.event_brand_uuid), 'get_payment'),
            # Everyone may fetch their own payment
            (Allow, 'role:user:%s' % self.paymentInstance.user.uuid, 'get_payment'),
            # Everyone may initiate their own payment(but admins can't initiate others payments)
            (Allow, 'role:user:%s' % self.paymentInstance.user.uuid, 'initiate_payment')
        ]

    def __init__(self, request, uuid):
        self.request = request
        self.paymentInstance = request.db.query(Payment) \
            .options(joinedload(Payment.event)) \
            .filter(Payment.uuid == uuid) \
            .first()

        if self.paymentInstance is None:
            raise HTTPNotFound("Payment not found")

@view_config(context=PaymentInstanceResource, name='', request_method='GET', renderer='json', permission='get_payment')
def get_payment(context, request):
    return context.paymentInstance

@view_config(context=PaymentInstanceResource, name='initiate', request_method='POST', renderer='json', permission='initiate_payment')
def initiate_payment(context, request):
    if context.paymentInstance.state != PaymentState.created:
        request.response.status = 400
        return {
            "error": "Payment is already initiated"
        }

    context.paymentInstance.state = PaymentState.initiated
    request.db.add(context.paymentInstance)
    # Bootstraps the payment with our external provider
    if context.paymentInstance.provider == PaymentProvider.vipps:
        if 'fallback_url' not in request.json_body:
            request.response.status = 400
            return {
                "error": "The variable fallback_url must be provided when making payments using vipps"
            }
        deeplinkUrl, slug = initialize_vipps_payment(request, context.paymentInstance, request.json_body['fallback_url'])

        if deeplinkUrl:
            # Since the payment is successful, insert everything. This populates payment.uuid
            request.db.flush()
            return {'url': deeplinkUrl, 'slug': slug}
        else:
            log.warn("Failed to create vipps payment")
            request.response.status = 500
            return {
                "error": "Failed to create vipps payment"
            }
    elif context.paymentInstance.provider == PaymentProvider.stripe:
        client_secret = initialize_stripe_payment(request, context.paymentInstance)
        request.db.flush()
        return {'client_secret': client_secret}
    elif context.paymentInstance.provider == PaymentProvider.free:
        store_session = context.paymentInstance.store_session
        if store_session is None or datetime.now() > store_session.expires:
            request.response.status = 400
            return {
                "error": "The store session has expired. Please create a new order"
            }

        if context.paymentInstance.price > 0 or store_session.get_total() > 0:
            log.error("User %s (%s) tried to get non-free tickets for free: %s" % (
                request.user.uuid,
                request.user.email,
                ", ".join(entry.ticket_type.name for entry in store_session.cart_entries)
            ))
            request.response.status = 400
            return {
                "error": "This cart is not free"
            }

        # Nothing to pay - mint the tickets right away
        mint_tickets(request, context.paymentInstance)
        return context.paymentInstance
    else:
        request.response.status = 400
        return {
            "error": "Payment type not yet supported"
        }
