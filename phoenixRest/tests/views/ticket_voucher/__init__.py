from phoenixRest.models.core.event import Event

from datetime import datetime

def test_ticket_voucher_flow(testapp):
    testapp.ensure_typical_event()

    # test is an admin
    sender_token, refresh = testapp.auth_get_tokens('test', 'sixcharacters')
    receiver_token, refresh = testapp.auth_get_tokens('jeff', 'sixcharacters')
    third_party_token, refresh = testapp.auth_get_tokens('adam', 'sixcharacters')

    sender_user = testapp.get_user(sender_token)
    receiver_user = testapp.get_user(receiver_token)
    third_party_user = testapp.get_user(third_party_token)

    # Current event
    current_event = testapp.get('/event/current', status=200).json_body
    assert current_event['uuid'] is not None

    # Get existing ticket types
    res = testapp.get('/event/%s/ticketType' % current_event['uuid'], headers=dict({
        'X-Phoenix-Auth': sender_token
    }), status=200)
    ticket_type = res.json_body[0]

    # Check how many tickets jeff has
    jeff_owned_tickets_pre = testapp.get('/user/%s/owned_tickets' % receiver_user['uuid'], headers=dict({
        'X-Phoenix-Auth': sender_token 
    }), status=200).json_body

    # Give jeff a voucher
    voucher = testapp.post_json('/ticket_voucher', dict({
        'ticket_type_uuid': ticket_type['uuid'],
        'recipient_user_uuid': receiver_user['uuid'],
        'last_use_event_uuid': current_event['uuid']
    }), headers=dict({
        'X-Phoenix-Auth': sender_token
    }), status=200).json_body

    # Check that jeff hasn't gotten a ticket yet
    jeff_owned_tickets_post = testapp.get('/user/%s/owned_tickets' % receiver_user['uuid'], headers=dict({
        'X-Phoenix-Auth': sender_token 
    }), status=200).json_body
    assert len(jeff_owned_tickets_pre) == len(jeff_owned_tickets_post)

    # Ensure third party can't burn the voucher
    res = testapp.post_json('/ticket_voucher/%s/burn' % voucher['uuid'], dict({
    }), headers=dict({
        'X-Phoenix-Auth': third_party_token
    }), status=403)

    # Ensure that recipient can burn it
    post_burn_voucher = testapp.post_json('/ticket_voucher/%s/burn' % voucher['uuid'], dict({
    }), headers=dict({
        'X-Phoenix-Auth': receiver_token
    }), status=200).json_body

    # Ensure that jeff has received a ticket
    jeff_owned_tickets_post = testapp.get('/user/%s/owned_tickets' % receiver_user['uuid'], headers=dict({
        'X-Phoenix-Auth': sender_token 
    }), status=200).json_body
    assert len(jeff_owned_tickets_pre) + 1 == len(jeff_owned_tickets_post)

    assert post_burn_voucher['ticket'] is not None
    assert post_burn_voucher['ticket']['event']['uuid'] == current_event['uuid']

def test_expired_voucher_flow(testapp, db):
    testapp.ensure_typical_event()

    # test is an admin
    sender_token, refresh = testapp.auth_get_tokens('test', 'sixcharacters')
    receiver_token, refresh = testapp.auth_get_tokens('jeff', 'sixcharacters')

    sender_user = testapp.get_user(sender_token)
    receiver_user = testapp.get_user(receiver_token)

    # Current event
    current_event = testapp.get('/event/current', status=200).json_body
    assert current_event['uuid'] is not None
    
    # Find an old event
    old_event = db.query(Event).filter(Event.end_time < datetime.now()).first()

    # Get existing ticket types
    res = testapp.get('/event/%s/ticketType' % current_event['uuid'], headers=dict({
        'X-Phoenix-Auth': sender_token
    }), status=200)
    ticket_type = res.json_body[0]

    # Check how many tickets jeff has
    jeff_owned_tickets_pre = testapp.get('/user/%s/owned_tickets' % receiver_user['uuid'], headers=dict({
        'X-Phoenix-Auth': sender_token 
    }), status=200).json_body

    # Give jeff a voucher
    voucher = testapp.post_json('/ticket_voucher', dict({
        'ticket_type_uuid': ticket_type['uuid'],
        'recipient_user_uuid': receiver_user['uuid'],
        'last_use_event_uuid': str(old_event.uuid),
    }), headers=dict({
        'X-Phoenix-Auth': sender_token
    }), status=200).json_body


    # Ensure that you cannot burn an expired voucher
    post_burn_voucher = testapp.post_json('/ticket_voucher/%s/burn' % voucher['uuid'], dict({
    }), headers=dict({
        'X-Phoenix-Auth': receiver_token
    }), status=400).json_body

    # Check that jeff didn't get a ticket
    jeff_owned_tickets_post = testapp.get('/user/%s/owned_tickets' % receiver_user['uuid'], headers=dict({
        'X-Phoenix-Auth': sender_token 
    }), status=200).json_body
    assert len(jeff_owned_tickets_pre) == len(jeff_owned_tickets_post)
