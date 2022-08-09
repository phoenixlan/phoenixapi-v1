from phoenixRest.models.tickets.payment import Payment, PaymentState
from phoenixRest.models.tickets.ticket import Ticket
from phoenixRest.models import db

import logging
log = logging.getLogger(__name__)

def mint_tickets(payment: Payment):
    if payment.store_session is None:
        raise RuntimeError("Tried to mint tickets on a payment that is already detatched from a store session")
    # Store that we received a websocket callback, such that an operator can see proof that we received payment.
    payment.state = PaymentState.paid
    db.flush()

    for entry in payment.store_session.cart_entries:
        for i in range(0, entry.amount):
            ticket = Ticket(payment.user, payment, entry.ticket_type)
            db.add(ticket)
            # Probably not neccesary either?
            #payment.tickets.append(ticket)
        log.info("Minted %s tickets of type %s for user %s" % (entry.amount, entry.ticket_type.name, payment.user_uuid))

    # TODO do we need this?
    #db.add(payment)

    # Free up store session
    for entry in payment.store_session.cart_entries:
        db.delete(entry)
    db.delete(payment.store_session)
    # Mark the payment as completed - tickets are minted
    payment.state = PaymentState.tickets_minted
    