# Test if we can reserve a store session
def test_create_store_session(testapp, upcoming_event, ticket_types, admin_user):
    token, refresh = testapp.auth_get_tokens(admin_user.email, 'sixcharacters')

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
    }), status=200)

    assert res.json_body['uuid'] is not None

def test_store_session_rejects_ticket_type_from_other_brand(
        testapp, upcoming_event, other_ticket_type, admin_token):
    response = testapp.put_json(
        '/event/%s/store_session' % upcoming_event.uuid,
        {
            'cart': [{'qty': 1, 'uuid': str(other_ticket_type.uuid)}]
        },
        headers={'Authorization': "Bearer " + admin_token},
        status=400
    )

    assert response.json_body['error'] == \
        'Ticket type belongs to a different event brand'

def _create_store_session(testapp, event, ticket_type, token):
    res = testapp.put_json('/event/%s/store_session' % event.uuid, dict({
        'cart': [
            {'qty': 1, 'uuid': str(ticket_type.uuid)}
        ]
    }), headers=dict({
        "Authorization": "Bearer " + token
    }), status=200)
    return res.json_body['uuid']

def test_free_payment_flow(testapp, upcoming_event, free_ticket_type, admin_user, admin_token):
    store_session = _create_store_session(testapp, upcoming_event, free_ticket_type, admin_token)

    res = testapp.post_json('/store_session/%s/payment' % store_session, dict({
        'provider': 'free'
    }), headers=dict({
        "Authorization": "Bearer " + admin_token
    }), status=200)
    assert res.json_body['price'] == 0
    payment_uuid = res.json_body['uuid']

    # Initiating a free payment mints the tickets right away
    res = testapp.post_json('/payment/%s/initiate' % payment_uuid, dict({}), headers=dict({
        "Authorization": "Bearer " + admin_token
    }), status=200)
    assert res.json_body['state'] == "PaymentState.tickets_minted"

    res = testapp.get('/user/%s/purchased_tickets' % admin_user.uuid, headers=dict({
        "Authorization": "Bearer " + admin_token
    }), status=200)
    minted = [ticket for ticket in res.json_body if ticket['payment_uuid'] == payment_uuid]
    assert len(minted) == 1
    assert minted[0]['ticket_type']['uuid'] == str(free_ticket_type.uuid)

def test_free_payment_rejected_for_paid_cart(testapp, upcoming_event, non_membership_ticket_type, admin_token):
    store_session = _create_store_session(testapp, upcoming_event, non_membership_ticket_type, admin_token)

    res = testapp.post_json('/store_session/%s/payment' % store_session, dict({
        'provider': 'free'
    }), headers=dict({
        "Authorization": "Bearer " + admin_token
    }), status=400)
    assert res.json_body['error'] == "This cart is not free"

def test_free_payment_initiate_rejected_when_cart_not_free(testapp, upcoming_event, free_ticket_type, admin_user, admin_token):
    store_session = _create_store_session(testapp, upcoming_event, free_ticket_type, admin_token)

    res = testapp.post_json('/store_session/%s/payment' % store_session, dict({
        'provider': 'free'
    }), headers=dict({
        "Authorization": "Bearer " + admin_token
    }), status=200)
    payment_uuid = res.json_body['uuid']

    # The ticket type stops being free before the payment is initiated
    free_ticket_type.price = 100

    res = testapp.post_json('/payment/%s/initiate' % payment_uuid, dict({}), headers=dict({
        "Authorization": "Bearer " + admin_token
    }), status=400)
    assert res.json_body['error'] == "This cart is not free"

    res = testapp.get('/user/%s/purchased_tickets' % admin_user.uuid, headers=dict({
        "Authorization": "Bearer " + admin_token
    }), status=200)
    assert not any(ticket['payment_uuid'] == payment_uuid for ticket in res.json_body)

def test_create_payment_other_users_store_session(testapp, upcoming_event, free_ticket_type, admin_token, jeff_user):
    store_session = _create_store_session(testapp, upcoming_event, free_ticket_type, admin_token)
    jeff_token, refresh = testapp.auth_get_tokens(jeff_user.email, 'sixcharacters')

    testapp.post_json('/store_session/%s/payment' % store_session, dict({
        'provider': 'free'
    }), headers=dict({
        "Authorization": "Bearer " + jeff_token
    }), status=403)

def test_create_payment_invalid_provider(testapp, upcoming_event, free_ticket_type, admin_token):
    store_session = _create_store_session(testapp, upcoming_event, free_ticket_type, admin_token)

    res = testapp.post_json('/store_session/%s/payment' % store_session, dict({
        'provider': 'bogus'
    }), headers=dict({
        "Authorization": "Bearer " + admin_token
    }), status=400)
    assert res.json_body['error'] == "Invalid payment provider"
