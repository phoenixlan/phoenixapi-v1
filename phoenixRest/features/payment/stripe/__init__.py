import stripe
import os
from phoenixRest.models.tickets.payment import Payment, PaymentState
from phoenixRest.models.tickets.payment_providers.stripe_payment import StripePayment

from phoenixRest.features.payment import mint_tickets

import logging
log = logging.getLogger(__name__)

STRIPE_INITIALIZED = False

STRIPE_ENDPOINT_SECRET = os.environ.get('STRIPE_ENDPOINT_SECRET', 'placeholder')

def initialize_stripe_payment(request, payment: Payment):
    # If we are running in pytest, we can safely mock
    if "PYTEST_CURRENT_TEST" in os.environ:
        return "placeholder client secret"
    # Only set API key when it is used, for testing purposes
    global STRIPE_INITIALIZED
    if not STRIPE_INITIALIZED:
        STRIPE_INITIALIZED = True
        stripe.api_key = os.environ["STRIPE_API_KEY"]

    amount = payment.price
    log.info("Creating payment of price %s" % amount)
    
    intent = stripe.PaymentIntent.create(
        amount=amount*100,
        currency='nok'
    )

    client_secret = intent['client_secret']
    payment_id = intent['id']
    log.info("Created new stripe payment with ID %s" % payment_id)

    request.db.add(StripePayment(payment, payment_id))

    return client_secret

# This should be called from the webhook
def finalize_stripe_payment(request, payment: StripePayment):
    # Mark it as paid
    payment.paid = True

    # Mint tickets
    mint_tickets(request, payment.payment)