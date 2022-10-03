from phoenixRest.models.tickets.payment import Payment, PaymentState
from phoenixRest.models.tickets.ticket import Ticket

import logging
log = logging.getLogger(__name__)

def mint_tickets(request, payment: Payment):
    if payment.store_session is None:
        raise RuntimeError("Tried to mint tickets on a payment that is already detatched from a store session")
    # Store that we received a websocket callback, such that an operator can see proof that we received payment.
    payment.state = PaymentState.paid
    request.db.flush()

    for entry in payment.store_session.cart_entries:
        for i in range(0, entry.amount):
            ticket = Ticket(payment.user, payment, entry.ticket_type, payment.event)
            request.db.add(ticket)
            # Probably not neccesary either?
            #payment.tickets.append(ticket)
        log.info("Minted %s tickets of type %s for user %s" % (entry.amount, entry.ticket_type.name, payment.user_uuid))

    # Send a mail
    request.mail_service.send_mail(payment.user.email, "Kvittering for kjøp av billetter", "tickets_minted.jinja2", {
        "mail": request.registry.settings["api.contact"],
        "name": request.registry.settings["api.name"],
        "payment": payment,
    })

    # Free up store session
    for entry in payment.store_session.cart_entries:
        request.db.delete(entry)
    request.db.delete(payment.store_session)
    # Mark the payment as completed - tickets are minted
    payment.state = PaymentState.tickets_minted

    