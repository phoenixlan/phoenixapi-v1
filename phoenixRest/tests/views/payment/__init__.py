from phoenixRest.models.core.event import Event
from phoenixRest.models.tickets.payment import Payment, PaymentProvider, PaymentState
from phoenixRest.models.tickets.ticket import Ticket
from phoenixRest.models.tickets.ticket_voucher import TicketVoucher

from phoenixRest.services.mail import MailService

from phoenixRest.features.payment.vipps import VIPPS_CALLBACK_AUTH_TOKEN

import transaction

from datetime import datetime, timedelta

def _create_store_session(testapp, event, token):
    res = testapp.get('/event/%s/ticketType' % event.uuid, headers=dict({
        "Authorization": "Bearer " + token
    }), status=200)

    # Reserve a card for the first ticket for sale, i guess
    res = testapp.put_json('/event/%s/store_session' % event.uuid, dict({
        'cart': [
            {'qty': 1, 'uuid': res.json_body[0]['uuid']}
        ]
    }), headers=dict({
        "Authorization": "Bearer " + token
    }), status=200)

    store_session = res.json_body['uuid']

    assert store_session is not None
    return store_session

def test_ticket_sale_start_limit(testapp, db, upcoming_event, ticket_types, jeff_user):
    # Jeff doesn't have permission to buy tickets any time
    token, refresh = testapp.auth_get_tokens(jeff_user.email, 'sixcharacters')

    # Make sure buying tickets is illegal
    event_instance = db.query(Event).filter(Event.uuid == upcoming_event.uuid).first()
    event_instance.booking_time = datetime.now() + timedelta(days=1)
    transaction.commit()

    res = testapp.get('/event/%s/ticketType' % upcoming_event.uuid, headers=dict({
        "Authorization": "Bearer " + token
    }), status=200)

    # Reserve a card for the first ticket for sale, i guess
    res = testapp.put_json('/event/%s/store_session' % upcoming_event.uuid, dict({
        'cart': [
            {'qty': 1, 'uuid': res.json_body[0]['uuid']}
        ]
    }), headers=dict({
        "Authorization": "Bearer " + token
    }), status=400)

def test_payment_requires_membership_personalia(testapp, upcoming_event, membership_ticket_type, admin_user):
    """Paying for a ticket that grants membership requires membership personalia"""
    token, refresh = testapp.auth_get_tokens(admin_user.email, 'sixcharacters')

    res = testapp.put_json('/event/%s/store_session' % upcoming_event.uuid, dict({
        'cart': [
            {'qty': 1, 'uuid': str(membership_ticket_type.uuid)}
        ]
    }), headers=dict({
        "Authorization": "Bearer " + token
    }), status=200)
    store_session = res.json_body['uuid']

    res = testapp.post_json('/store_session/%s/payment' % store_session, dict({
        'provider': 'vipps'
    }), headers=dict({
        "Authorization": "Bearer " + token
    }), status=400)
    assert 'membership personalia' in res.json_body['error']

# Test if we can create a payment
def test_payment_flow_vipps(testapp, upcoming_event, ticket_types, admin_user, admin_membership_personalia):
    token, refresh = testapp.auth_get_tokens(admin_user.email, 'sixcharacters')

    store_session = _create_store_session(testapp, upcoming_event, token)
    # Create a payment
    res = testapp.post_json('/store_session/%s/payment' % store_session, dict({
        'provider': 'vipps'
    }), headers=dict({
        "Authorization": "Bearer " + token
    }), status=200)
    
    #self.assertIsNotNone(res.json_body['url'])
    #self.assertIsNotNone(res.json_body['slug'])
    #self.assertIsNotNone(res.json_body['payment_uuid'])
    assert res.json_body['uuid'] is not None

    payment_uuid = res.json_body['uuid']

    # Initiate the payment with vipps
    res = testapp.post_json('/payment/%s/initiate' % payment_uuid, dict({
        'fallback_url': "https://test.phoenix.no"
    }), headers=dict({
        "Authorization": "Bearer " + token
    }), status=200)
    assert res.json_body['url'] is not None
    assert res.json_body['slug'] is not None

    vipps_slug = res.json_body['slug']

    # Test that the ticket state is correct at this point
    res = testapp.get('/payment/%s' % payment_uuid,
        headers=dict({
            "Authorization": "Bearer " + token
        }),
        status=200)
    assert res.json_body['state'] == "PaymentState.initiated"

    # Send the webhook
    # Test response payload from https://www.vipps.no/developers-documentation/ecom/documentation#callbacks
    res = testapp.post_json('/hooks/vipps/v2/payments/%s' % vipps_slug, dict({
        "merchantSerialNumber": 123456,
        "orderId": vipps_slug,
        "transactionInfo": {
            "amount": 20000,
            "status": "SALE",
            "timeStamp": "2018-12-12T11:18:38.246Z",
            "transactionId": "5001420062"
        }
    }), headers=dict({
        'Authorization': VIPPS_CALLBACK_AUTH_TOKEN
    }), status=200)

    # Tickets should now exist, so lets look for a ticket minted from this payment
    user_uuid = testapp.get_user(token)['uuid']
    print("User uuid: %s" % user_uuid)
    
    res = testapp.get('/user/%s/purchased_tickets' % user_uuid, headers=dict({
        "Authorization": "Bearer " + token
    }), status=200)

    exists = False
    for ticket in res.json_body:
        if ticket['payment_uuid'] == payment_uuid:
            exists = True

    assert exists
    # Ensure payments exists as well
    res = testapp.get('/user/%s/payments' % user_uuid, headers=dict({
        "Authorization": "Bearer " + token
    }))

    exists = False
    for payment in res.json_body:
        if payment['uuid'] == payment_uuid:
            exists = True

    assert exists
    

# Test if we can create a payment
def test_payment_flow_stripe(testapp, upcoming_event, ticket_types, admin_user, admin_membership_personalia):
    token, refresh = testapp.auth_get_tokens(admin_user.email, 'sixcharacters')

    store_session = _create_store_session(testapp, upcoming_event, token)
    # Create a payment
    res = testapp.post_json('/store_session/%s/payment' % store_session, dict({
        'provider': 'stripe'
    }), headers=dict({
        "Authorization": "Bearer " + token
    }), status=200)
    
    assert res.json_body['uuid'] is not None

    payment_uuid = res.json_body['uuid']

    res = testapp.post_json('/payment/%s/initiate' % payment_uuid, dict({
        'fallback_url': "https://test.phoenix.no"
    }), headers=dict({
        "Authorization": "Bearer " + token
    }), status=200)
    assert res.json_body['client_secret'] is not None

    # Test that the ticket state is correct at this point
    res = testapp.get('/payment/%s' % payment_uuid,
        headers=dict({
            "Authorization": "Bearer " + token
        }),
        status=200)
    assert res.json_body['state'] == "PaymentState.initiated"

    # TODO test webhook

def test_refund_partial_then_full(testapp, db, admin_token, jeff_stripe_payment, non_membership_ticket_type):
    """Refunding one ticket at a time first partially refunds, then fully refunds the payment"""
    first, second = [ ticket.ticket_id for ticket in jeff_stripe_payment.tickets ]

    res = testapp.post_json('/payment/%s/refund' % jeff_stripe_payment.uuid, {
        'tickets': [first]
    }, headers={'Authorization': "Bearer " + admin_token}, status=200)
    assert res.json_body['state'] == "PaymentState.partially_refunded"
    assert res.json_body['refunded_amount'] == non_membership_ticket_type.price
    assert [ ticket.ticket_id for ticket in jeff_stripe_payment.tickets ] == [second]
    assert db.query(Ticket).filter(Ticket.ticket_id == first).first() is None

    res = testapp.post_json('/payment/%s/refund' % jeff_stripe_payment.uuid, {
        'tickets': [second]
    }, headers={'Authorization': "Bearer " + admin_token}, status=200)
    assert res.json_body['state'] == "PaymentState.refunded"
    assert res.json_body['refunded_amount'] == jeff_stripe_payment.price
    assert jeff_stripe_payment.tickets == []

def test_refund_full_vipps(testapp, admin_token, jeff_vipps_payment):
    res = testapp.post_json('/payment/%s/refund' % jeff_vipps_payment.uuid, {
        'tickets': [ ticket.ticket_id for ticket in jeff_vipps_payment.tickets ]
    }, headers={'Authorization': "Bearer " + admin_token}, status=200)
    assert res.json_body['state'] == "PaymentState.refunded"
    assert res.json_body['refunded_amount'] == jeff_vipps_payment.price

def test_refund_after_manual_deletion_is_full(testapp, db, admin_token, jeff_stripe_payment):
    """A ticket deleted manually means the remaining ticket is all that's left, so refunding it is a full refund"""
    first, second = jeff_stripe_payment.tickets
    db.delete(first)
    db.flush()
    db.expire(jeff_stripe_payment, ['tickets'])

    res = testapp.post_json('/payment/%s/refund' % jeff_stripe_payment.uuid, {
        'tickets': [second.ticket_id]
    }, headers={'Authorization': "Bearer " + admin_token}, status=200)
    assert res.json_body['state'] == "PaymentState.refunded"

def test_refund_free_payment(testapp, db, admin_token, jeff_user, free_ticket_type, upcoming_event):
    free_ticket_type.refundable = True
    payment = Payment(jeff_user, PaymentProvider.free, 0, upcoming_event)
    payment.state = PaymentState.tickets_minted
    ticket = Ticket(jeff_user, payment, free_ticket_type, upcoming_event)
    db.add_all([payment, ticket])
    db.flush()

    res = testapp.post_json('/payment/%s/refund' % payment.uuid, {
        'tickets': [ticket.ticket_id]
    }, headers={'Authorization': "Bearer " + admin_token}, status=200)
    assert res.json_body['state'] == "PaymentState.refunded"
    assert res.json_body['refunded_amount'] == 0

def test_refund_validates_tickets(testapp, admin_token, jeff_stripe_payment, jeff_vipps_payment):
    ticket_id = jeff_stripe_payment.tickets[0].ticket_id
    url = '/payment/%s/refund' % jeff_stripe_payment.uuid
    headers = {'Authorization': "Bearer " + admin_token}

    testapp.post_json(url, {}, headers=headers, status=400)
    testapp.post_json(url, {'tickets': []}, headers=headers, status=400)
    testapp.post_json(url, {'tickets': [str(ticket_id)]}, headers=headers, status=400)
    testapp.post_json(url, {'tickets': [ticket_id, ticket_id]}, headers=headers, status=400)
    # A ticket from another payment
    testapp.post_json(url, {'tickets': [jeff_vipps_payment.tickets[0].ticket_id]}, headers=headers, status=400)

    assert len(jeff_stripe_payment.tickets) == 2

def test_refund_requires_minted_tickets(testapp, admin_token, jeff_stripe_payment):
    jeff_stripe_payment.state = PaymentState.initiated

    testapp.post_json('/payment/%s/refund' % jeff_stripe_payment.uuid, {
        'tickets': [jeff_stripe_payment.tickets[0].ticket_id]
    }, headers={'Authorization': "Bearer " + admin_token}, status=400)

def test_refund_rejects_non_refundable_ticket_type(testapp, admin_token, jeff_stripe_payment, non_membership_ticket_type):
    non_membership_ticket_type.refundable = False

    testapp.post_json('/payment/%s/refund' % jeff_stripe_payment.uuid, {
        'tickets': [jeff_stripe_payment.tickets[0].ticket_id]
    }, headers={'Authorization': "Bearer " + admin_token}, status=400)

def test_refund_rejects_checked_in_ticket(testapp, admin_token, jeff_stripe_payment):
    ticket = jeff_stripe_payment.tickets[0]
    ticket.checked_in = datetime.now()

    testapp.post_json('/payment/%s/refund' % jeff_stripe_payment.uuid, {
        'tickets': [ticket.ticket_id]
    }, headers={'Authorization': "Bearer " + admin_token}, status=400)

def test_refund_rejects_voucher_ticket(testapp, db, admin_token, admin_user, jeff_user, jeff_stripe_payment, upcoming_event):
    ticket = jeff_stripe_payment.tickets[0]
    voucher = TicketVoucher(admin_user, jeff_user, ticket.ticket_type, upcoming_event.event_brand, upcoming_event)
    voucher.ticket = ticket
    db.add(voucher)
    db.flush()

    testapp.post_json('/payment/%s/refund' % jeff_stripe_payment.uuid, {
        'tickets': [ticket.ticket_id]
    }, headers={'Authorization': "Bearer " + admin_token}, status=400)

def test_refund_exceeding_payment_total_fails(testapp, admin_token, jeff_stripe_payment):
    """If ticket prices add up to more than what was paid, something is misconfigured"""
    jeff_stripe_payment.price = 1

    testapp.post_json('/payment/%s/refund' % jeff_stripe_payment.uuid, {
        'tickets': [jeff_stripe_payment.tickets[0].ticket_id]
    }, headers={'Authorization': "Bearer " + admin_token}, status=500)

    assert len(jeff_stripe_payment.tickets) == 2
    assert jeff_stripe_payment.refunded_amount == 0

def test_refund_permissions(testapp, jeff_user, ticket_admin_user, jeff_stripe_payment):
    url = '/payment/%s/refund' % jeff_stripe_payment.uuid
    body = {'tickets': [jeff_stripe_payment.tickets[0].ticket_id]}

    # Buyers can't refund their own payments
    token, refresh = testapp.auth_get_tokens(jeff_user.email, 'sixcharacters')
    testapp.post_json(url, body, headers={'Authorization': "Bearer " + token}, status=403)

    token, refresh = testapp.auth_get_tokens(ticket_admin_user.email, 'sixcharacters')
    testapp.post_json(url, body, headers={'Authorization': "Bearer " + token}, status=200)

def test_refund_rejects_ticket_not_owned_by_buyer(testapp, admin_token, adam_user, jeff_stripe_payment):
    """Anti-scam measure: tickets handed to someone else can't be refunded"""
    transferred = jeff_stripe_payment.tickets[0]
    transferred.owner = adam_user

    testapp.post_json('/payment/%s/refund' % jeff_stripe_payment.uuid, {
        'tickets': [transferred.ticket_id]
    }, headers={'Authorization': "Bearer " + admin_token}, status=400)

    assert len(jeff_stripe_payment.tickets) == 2

def test_refund_mails_buyer(testapp, monkeypatch, admin_token, jeff_user, jeff_stripe_payment):
    sent_to = []
    monkeypatch.setattr(MailService, '_send_mail_impl', lambda self, to, subject, body: sent_to.append(to))

    testapp.post_json('/payment/%s/refund' % jeff_stripe_payment.uuid, {
        'tickets': [jeff_stripe_payment.tickets[0].ticket_id]
    }, headers={'Authorization': "Bearer " + admin_token}, status=200)

    assert sent_to == [jeff_user.email]
