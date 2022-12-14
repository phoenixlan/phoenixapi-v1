from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPBadRequest,
    HTTPNotFound,
    HTTPInternalServerError
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow


from phoenixRest.models.crew.crew import Crew
from phoenixRest.models.tickets.payment import Payment, PaymentProvider, PaymentState
from phoenixRest.models.tickets.ticket_type import TicketType
from phoenixRest.models.tickets.store_session import StoreSession

from phoenixRest.models.tickets.payment_providers.stripe_payment import StripePayment
from phoenixRest.models.tickets.payment_providers.vipps_payment import VippsPayment

from phoenixRest.utils import validate
from phoenixRest.resource import resource

from phoenixRest.roles import ADMIN, TICKET_ADMIN

from phoenixRest.views.crew.instance import CrewInstanceViews

from phoenixRest.features.payment.vipps import VIPPS_CALLBACK_AUTH_TOKEN, finalize_vipps_payment, capture_vipps_payment
from phoenixRest.features.payment.stripe import STRIPE_ENDPOINT_SECRET, finalize_stripe_payment

import stripe

import transaction

from datetime import datetime

import logging
log = logging.getLogger(__name__)

@resource(name='hooks')
class HookResource(object):
    def __acl__(self):
        acl = [
            (Allow, Everyone, 'stripe')
            # Authenticated pages
            #(Allow, Authenticated, Authenticated),
            #(Deny, Everyone, Authenticated),
        ]
        # Support vipps callbacks
        if self.request.path.lower().startswith("/hooks/vipps"):
            if self.request.headers.get('Authorization', None) == VIPPS_CALLBACK_AUTH_TOKEN:
                acl.append((Allow, Everyone, 'vipps'))
        return acl

    def __init__(self, request):
        self.request = request

@view_config(context=HookResource, name='stripe', request_method='POST', renderer='json', permission='stripe')
def stripe_hook(context, request):
    sig_header = request.headers.get('stripe-signature', '')
    try:
        event = stripe.Webhook.construct_event(
            request.body.decode('ascii'), sig_header, STRIPE_ENDPOINT_SECRET
        )
    except ValueError as e:
        log.warn("Unable to decode stripe webhook")
        request.response.status = 400
        return {
            "error": "Failed to decode"
        }
    except stripe.error.SignatureVerificationError as e:
        request.response.status = 400
        log.error("GOT INVALID SIGNATURE VERIFICATION!")
        return {
            "error": "Invalid signature"
        }

    if event.type != 'payment_intent.succeeded':
        log.warn("Rejected a stripe hook with invalid type")
        request.response.status = 400
        return {
            'error': "Invalid type"
        }
    # stripe payment 
    payment_id = event.data.object.id
    payment = request.db.query(StripePayment).filter(StripePayment.payment_id == payment_id).first()

    if payment is None:
        log.warn("Payment not found!")
        request.response.status = 404
        return {
            'error': 'Payment not found'
        }

    finalize_stripe_payment(request, payment)
    return payment.payment

#/v2/payments/{orderId}
@view_config(context=HookResource, name='vipps', request_method='POST', renderer='string', permission='vipps')
def vipps_hook(context, request):
    log.info("Got vipps hook: %s" % request.body)
    transaction_info = request.json_body['transactionInfo']
    order_id = request.subpath[2]

    vipps_payment = request.db.query(VippsPayment).filter(VippsPayment.slug == order_id).first()
    if not vipps_payment:
        log.warning("Tried to update a vipps payment that doesn't exist")
        raise HTTPNotFound()
    
    status = transaction_info['status']
    vipps_payment.state = status
    request.db.flush()

    if status == "SALE":
        # Extra security checks
        if vipps_payment.payment.state != PaymentState.initiated:
            log.warning("Security issue: tried to activate a payment that was not in state: initiated")
            raise HTTPBadRequest("Tried to request a hook on a payment which has already gotten a callback")
        finalize_vipps_payment(request, vipps_payment)
        log.info("Successfully registered vipps sale")
    elif status == "REJECTED":
        vipps_payment.payment.state = PaymentState.failed
        request.db.add(vipps_payment.payment)
        log.info("Registered rejected vipps sale")
    elif status == "CANCELLED":
        vipps_payment.payment.state = PaymentState.failed
        request.db.add(vipps_payment.payment)
        log.info("Registered cancelled vipps sale")
    elif status == "RESERVED":
        log.info("Got a reserved transaction, capturing the amout and making the purchase")
        if vipps_payment.payment.state != PaymentState.initiated:
            log.warning("Security issue: tried to activate a payment that was not in state: initiated")
            raise HTTPBadRequest("Tried to request a hook on a payment which has already gotten a callback")
        if capture_vipps_payment(vipps_payment):
            finalize_vipps_payment(request, vipps_payment)
            log.info("Successfully registered vipps sale")
        else:
            log.error("Unable to capture VIPPS sale, no ticket is minted")
    else:
        log.error("Got vipps transaction status which is not supported: %s" % status)
        raise HTTPInternalServerError("Unknown status")
    
    return "OK"
    


    
