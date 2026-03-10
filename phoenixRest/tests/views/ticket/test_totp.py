
from phoenixRest.tests.views.ticket.test_seating import ensure_ticket

import time

def test_totp_generated_when_none_exists(testapp, upcoming_event):
    testapp.ensure_typical_event()
    token, refresh = testapp.auth_get_tokens('test@example.com', 'sixcharacters')

    current_event = testapp.get('/event/current', status=200).json_body
    ticket = ensure_ticket(testapp, token, current_event['uuid'])

    # Get totp - should generate one since none exists
    res = testapp.get('/ticket/%s/totp' % ticket['ticket_id'], headers=dict({
        "Authorization": "Bearer " + token
    }), status=200).json_body

    assert res['totp'] is not None

def test_totp_idempotent(testapp, upcoming_event):
    testapp.ensure_typical_event()
    token, refresh = testapp.auth_get_tokens('test@example.com', 'sixcharacters')

    current_event = testapp.get('/event/current', status=200).json_body
    ticket = ensure_ticket(testapp, token, current_event['uuid'])

    # Get totp twice
    res1 = testapp.get('/ticket/%s/totp' % ticket['ticket_id'], headers=dict({
        "Authorization": "Bearer " + token
    }), status=200).json_body

    res2 = testapp.get('/ticket/%s/totp' % ticket['ticket_id'], headers=dict({
        "Authorization": "Bearer " + token
    }), status=200).json_body

    assert res1['totp'] == res2['totp']

def test_totp_forbidden_for_non_owner(testapp, upcoming_event):
    testapp.ensure_typical_event()
    owner_token, refresh = testapp.auth_get_tokens('test@example.com', 'sixcharacters')
    other_token, refresh = testapp.auth_get_tokens('jeff@example.com', 'sixcharacters')

    current_event = testapp.get('/event/current', status=200).json_body
    ticket = ensure_ticket(testapp, owner_token, current_event['uuid'])

    # Non-owner should get 403
    testapp.get('/ticket/%s/totp' % ticket['ticket_id'], headers=dict({
        "Authorization": "Bearer " + other_token
    }), status=403)

def test_totp_reset_after_transfer(testapp, upcoming_event):
    testapp.ensure_typical_event()
    sender_token, refresh = testapp.auth_get_tokens('test@example.com', 'sixcharacters')
    receiver_token, refresh = testapp.auth_get_tokens('jeff@example.com', 'sixcharacters')

    receiver_user = testapp.get_user(receiver_token)

    current_event = testapp.get('/event/current', status=200).json_body
    ticket = ensure_ticket(testapp, sender_token, current_event['uuid'])

    # Get totp before transfer
    totp_before = testapp.get('/ticket/%s/totp' % ticket['ticket_id'], headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200).json_body

    # Wait for the transfer expiry to pass (paste_pytest.ini has 4s expiry)
    time.sleep(5)

    # Transfer the ticket
    testapp.post_json('/ticket/%s/transfer' % ticket['ticket_id'], dict({
        'user_email': receiver_user['email']
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200)

    # New owner gets totp - should be a new one
    totp_after = testapp.get('/ticket/%s/totp' % ticket['ticket_id'], headers=dict({
        "Authorization": "Bearer " + receiver_token
    }), status=200).json_body

    assert totp_after['totp'] is not None
    assert totp_before['totp'] != totp_after['totp']
