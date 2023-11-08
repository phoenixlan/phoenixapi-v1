from phoenixRest.features.vipps import _get_payment_str

from phoenixRest.models.core.event import get_current_event
from phoenixRest.models.tickets.store_session import StoreSession
from phoenixrest.models.tickets.ticket_type import TicketType
from phoenixRest.models.tickets.store_session_cart_entry import StoreSessionCartEntry

from phoenixRest.models.tickets.payment import Payment, PaymentState, PaymentProvider

from phoenixRest.models.core.user import User

def test_normal_payment_str(db):
    user = db.query(User).filter(User.firstname == "Jeff").first()
    store_session = StoreSession(user, 1000)

    # Get some ticket types
    vestibyle = db.query(TicketType).filter(TicketType.name == "Vestibyle").first()

    # Create cart entry
    store_session.cart_entries.append(StoreSessionCartEntry(vestibyle, 1))

    # Create payment
    payment = Payment(user, PaymentProvider.vipps, store_session.get_total(), get_current_event(request))