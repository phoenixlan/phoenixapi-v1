from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPBadRequest,
    HTTPNotFound
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow

from phoenixRest.models.core.audit_log import AuditLog
from phoenixRest.models.tickets.payment import Payment, PaymentState, PaymentProvider
from phoenixRest.models.tickets.ticket_transfer import TicketTransfer
from phoenixRest.models.tickets.ticket_voucher import TicketVoucher

from phoenixRest.roles import ADMIN, TICKET_ADMIN, BRAND_ADMIN, TICKET_AUDIT

from phoenixRest.features.payment.vipps import initialize_vipps_payment, refund_vipps_payment
from phoenixRest.features.payment.stripe import initialize_stripe_payment, refund_stripe_payment
from phoenixRest.features.payment import mint_tickets

from phoenixRest.utils import validate

from sqlalchemy.orm import joinedload

from datetime import datetime

import logging
log = logging.getLogger(__name__)


class PaymentInstanceResource(object):
    def __acl__(self):
        return [
            (Allow, ADMIN(), 'get_payment'),
            (Allow, TICKET_ADMIN(self.paymentInstance.event.event_brand_uuid), 'get_payment'),
            (Allow, TICKET_AUDIT(self.paymentInstance.event.event_brand_uuid), 'get_payment'),

            # Admins can refund a payment, either partially or in full
            (Allow, ADMIN(), 'refund_payment'),
            (Allow, BRAND_ADMIN(self.paymentInstance.event.event_brand_uuid), 'refund_payment'),
            (Allow, TICKET_ADMIN(self.paymentInstance.event.event_brand_uuid), 'refund_payment'),

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

@view_config(context=PaymentInstanceResource, name='refund', request_method='POST', renderer='json', permission='refund_payment')
@validate(json_body={'tickets': list})
def refund_payment(context, request):
    """Allows one or more of the tickets in this payment to be refunded"""
    payment = context.paymentInstance
    ticket_ids = request.json_body['tickets']

    if len(ticket_ids) == 0 or any(type(ticket_id) != int for ticket_id in ticket_ids):
        request.response.status = 400
        return {
            'error': "Must provide a list of ticket IDs to be refunded"
        }

    if len(set(ticket_ids)) != len(ticket_ids):
        request.response.status = 400
        return {
            'error': "The same ticket can't be refunded twice"
        }

    if payment.state not in [PaymentState.tickets_minted, PaymentState.partially_refunded]:
        request.response.status = 400
        return {
            'error': "Only payments with minted tickets can be refunded"
        }

    # Tickets may have been refunded manually and deleted, so the payment's current tickets are the source of truth
    payment_tickets = { ticket.ticket_id: ticket for ticket in payment.tickets }

    for ticket_id in ticket_ids:
        if ticket_id not in payment_tickets:
            request.response.status = 400
            return {
                'error': "Ticket %s does not exist or does not belong to this payment" % ticket_id
            }
    tickets = [ payment_tickets[ticket_id] for ticket_id in ticket_ids ]

    for ticket in tickets:
        # Anti-scam measure: a ticket that has been handed to someone else must not be refundable by the buyer
        if ticket.owner != payment.user:
            request.response.status = 400
            return {
                'error': "Ticket %s is no longer owned by the buyer, and cannot be refunded" % ticket.ticket_id
            }
        if not ticket.ticket_type.refundable:
            request.response.status = 400
            return {
                'error': "Ticket %s is of a ticket type that is not refundable" % ticket.ticket_id
            }
        if ticket.checked_in is not None:
            request.response.status = 400
            return {
                'error': "Ticket %s is already checked in" % ticket.ticket_id
            }
        if request.db.query(TicketVoucher).filter(TicketVoucher.ticket_id == ticket.ticket_id).first() is not None:
            request.response.status = 400
            return {
                'error': "Ticket %s was created from a ticket voucher, and cannot be refunded" % ticket.ticket_id
            }

    is_full_refund = len(payment_tickets) == len(tickets)
    amount = sum(ticket.ticket_type.price for ticket in tickets)

    if amount + payment.refunded_amount > payment.price:
        log.error("Refusing to refund %s NOK for payment %s - it would exceed the payment total of %s NOK (%s NOK already refunded). This is likely a configuration bug, e.g. a ticket type price that changed after purchase" % (
            amount,
            payment.uuid,
            payment.price,
            payment.refunded_amount
        ))
        request.response.status = 500
        return {
            'error': "The refund would exceed the payment total. This is a configuration bug, please contact the developers"
        }

    if payment.provider == PaymentProvider.vipps:
        refunded = refund_vipps_payment(payment.vipps_payment, amount, len(tickets))
    elif payment.provider == PaymentProvider.stripe:
        refunded = refund_stripe_payment(payment.stripe_payment, amount)
    elif payment.provider == PaymentProvider.free:
        # Nothing was paid, so there is nothing to refund with a provider
        refunded = True
    else:
        request.response.status = 400
        return {
            'error': "Payment type not yet supported"
        }

    if not refunded:
        log.error("Failed to refund %s NOK for payment %s with %s" % (amount, payment.uuid, payment.provider))
        request.response.status = 500
        return {
            'error': "The payment provider failed to refund the payment"
        }

    # Snapshot what the e-mail needs before the tickets are deleted
    refunded_tickets = [ {
        'ticket_id': ticket.ticket_id,
        'ticket_type': ticket.ticket_type.name,
    } for ticket in tickets ]

    for ticket in tickets:
        if ticket.totp is not None:
            request.db.delete(ticket.totp)
        for transfer in request.db.query(TicketTransfer).filter(TicketTransfer.ticket == ticket).all():
            request.db.delete(transfer)
        request.db.delete(ticket)

    payment.refunded_amount += amount
    payment.state = PaymentState.refunded if is_full_refund else PaymentState.partially_refunded

    request.db.add(AuditLog(request.user, "payment_refund", {
        "payment_uuid": str(payment.uuid),
        "ticket_ids": ticket_ids,
        "amount": amount,
        "full_refund": is_full_refund
    }))
    request.db.flush()

    log.info("Refunded %s NOK (tickets %s) for payment %s" % (amount, ", ".join(str(ticket_id) for ticket_id in ticket_ids), payment.uuid))

    brand = payment.event.event_brand
    request.service_manager.get_service('email').send_mail(payment.user.email, "Refusjon av billetter", "refund_buyer.jinja2", {
        "mail": brand.contact_email,
        "name": brand.name,
        "tickets": refunded_tickets,
        "amount": amount,
        "full_refund": is_full_refund
    })

    request.db.expire(payment, ['tickets'])
    return payment


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
