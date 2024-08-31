from phoenixRest.features.payment.vipps import _get_payment_str

from phoenixRest.models.tickets.store_session import StoreSession
from phoenixRest.models.tickets.ticket_type import TicketType
from phoenixRest.models.tickets.store_session_cart_entry import StoreSessionCartEntry

from phoenixRest.models.tickets.payment import Payment, PaymentState, PaymentProvider

from phoenixRest.models.core.user import User

def test_normal_payment_singular_str(db, testapp):
    user = db.query(User).filter(User.firstname == "Jeff").first()
    store_session = StoreSession(user, 1000)

    # Get some ticket types
    vestibyle = db.query(TicketType).filter(TicketType.name == "Vestibyle").first()

    # Create cart entry
    store_session.cart_entries.append(StoreSessionCartEntry(vestibyle, 1))

    # Create payment
    payment = Payment(user, PaymentProvider.vipps, store_session.get_total(), testapp.get_current_event(db))
    # A payment is added later and need not be bound to store session apparently.
    # TODO: Maybe store session should be in the constructor?
    payment.store_session = store_session
    db.add(payment)

    payment_str = _get_payment_str(payment)

    assert payment_str == "1 Vestibyle-billett"

def test_normal_payment_plural_str(db, testapp):
    user = db.query(User).filter(User.firstname == "Jeff").first()
    store_session = StoreSession(user, 1000)

    # Get some ticket types
    vestibyle = db.query(TicketType).filter(TicketType.name == "Vestibyle").first()

    # Create cart entry
    store_session.cart_entries.append(StoreSessionCartEntry(vestibyle, 2))

    # Create payment
    payment = Payment(user, PaymentProvider.vipps, store_session.get_total(), testapp.get_current_event(db))
    # A payment is added later and need not be bound to store session apparently.
    # TODO: Maybe store session should be in the constructor?
    payment.store_session = store_session
    db.add(payment)

    payment_str = _get_payment_str(payment)

    assert payment_str == "2 Vestibyle-billetter"

def test_long_payment_str(db, testapp):
    user = db.query(User).filter(User.firstname == "Jeff").first()
    store_session = StoreSession(user, 1000)

    # Get some ticket types
    vestibyle = db.query(TicketType).filter(TicketType.name == "Vestibyle").first()
    multisal = db.query(TicketType).filter(TicketType.name == "Multisal").first()

    # Invent some weird non-ticket type to overflow things
    weirdType = TicketType("Weird long ticket type. it's a very long name. How long? Too long!", 20, "test type", False, False)
    db.add(weirdType)

    # Create cart entry
    store_session.cart_entries.append(StoreSessionCartEntry(vestibyle, 2))
    store_session.cart_entries.append(StoreSessionCartEntry(multisal, 3))
    store_session.cart_entries.append(StoreSessionCartEntry(weirdType, 7))

    # Create payment
    payment = Payment(user, PaymentProvider.vipps, store_session.get_total(), testapp.get_current_event(db))
    # A payment is added later and need not be bound to store session apparently.
    # TODO: Maybe store session should be in the constructor?
    payment.store_session = store_session
    db.add(payment)

    payment_str = _get_payment_str(payment)

    assert payment_str == "5 billetter, 7 annet"