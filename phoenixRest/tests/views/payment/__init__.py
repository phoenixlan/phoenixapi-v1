from phoenixRest.models.core.event import Event

from phoenixRest.features.payment.vipps import VIPPS_CALLBACK_AUTH_TOKEN

import transaction

from datetime import datetime, timedelta

def _create_store_session(testapp, token):
    res = testapp.get('/event/current', status=200)
    assert res.json_body['uuid'] is not None

    res = testapp.get('/event/%s/ticketType' % res.json_body['uuid'], headers=dict({
        "Authorization": "Bearer " + token
    }), status=200)

    # Reserve a card for the first ticket for sale, i guess
    res = testapp.put_json('/store_session', dict({
        'cart': [
            {'qty': 1, 'uuid': res.json_body[0]['uuid']}
        ]
    }), headers=dict({
        "Authorization": "Bearer " + token
    }), status=200)

    store_session = res.json_body['uuid']

    assert store_session is not None
    return store_session

def test_ticket_sale_start_limit(testapp, db, upcoming_event):
    testapp.ensure_typical_event()
    # Jeff doesn't have permission to buy tickets any time
    token, refresh = testapp.auth_get_tokens('jeff@example.com', 'sixcharacters')

    current_event = testapp.get('/event/current', status=200).json_body
    assert current_event['uuid'] is not None

    # Make sure buying tickets is illegal
    event_instance = db.query(Event).filter(Event.uuid == current_event['uuid']).first()
    event_instance.booking_time = datetime.now() + timedelta(days=1)
    transaction.commit()

    res = testapp.get('/event/%s/ticketType' % current_event['uuid'], headers=dict({
        "Authorization": "Bearer " + token
    }), status=200)

    # Reserve a card for the first ticket for sale, i guess
    res = testapp.put_json('/store_session', dict({
        'cart': [
            {'qty': 1, 'uuid': res.json_body[0]['uuid']}
        ]
    }), headers=dict({
        "Authorization": "Bearer " + token
    }), status=400)

# Test if we can create a payment
def test_payment_flow_vipps(testapp, upcoming_event):
    testapp.ensure_typical_event()
    token, refresh = testapp.auth_get_tokens('test@example.com', 'sixcharacters')

    store_session = _create_store_session(testapp, token)
    # Create a payment
    res = testapp.post_json('/payment', dict({
        'store_session': store_session,
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
def test_payment_flow_stripe(testapp, upcoming_event):
    testapp.ensure_typical_event()
    token, refresh = testapp.auth_get_tokens('test@example.com', 'sixcharacters')

    store_session = _create_store_session(testapp, token)
    # Create a payment
    res = testapp.post_json('/payment', dict({
        'store_session': store_session,
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

    
