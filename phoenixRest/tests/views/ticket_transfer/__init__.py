
def test_ticket_transfer_flow(testapp, upcoming_event, ticket_types):
    # test is an admin
    sender_token, refresh = testapp.auth_get_tokens('test@example.com', 'sixcharacters')
    receiver_token, refresh = testapp.auth_get_tokens('jeff@example.com', 'sixcharacters')
    receiver_2_token , refresh = testapp.auth_get_tokens('adam@example.com', 'sixcharacters')

    # Get user UUID
    sender_user = testapp.get_user(sender_token)
    receiver_user = testapp.get_user(receiver_token)
    receiver_2_user = testapp.get_user(receiver_2_token)

    # Get existing ticket types
    res = testapp.get('/event/%s/ticketType' % upcoming_event.uuid, headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200)
    ticket_type = res.json_body[0]

    # Give test a free ticket. Only works because test is an admin
    res = testapp.post_json('/ticket', dict({
        'ticket_type': ticket_type['uuid'],
        'recipient': sender_user['uuid'],
        "event_uuid": str(upcoming_event.uuid)
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200)

    # List the tickets owned by the test user
    owned_tickets = testapp.get('/user/%s/owned_tickets' % sender_user['uuid'], headers=dict({
        "Authorization": "Bearer " + sender_token 
    }), status=200).json_body
    assert len(owned_tickets) > 0

    # Get the tickets owned by the recipient prior to transfer
    owned_tickets_recipient = testapp.get('/user/%s/owned_tickets' % receiver_user['uuid'], headers=dict({
        "Authorization": "Bearer " + receiver_token
    }), status=200).json_body

    transfer_ticket = owned_tickets[0]

    # Someone who doesn't own a ticket can't transfer it
    res = testapp.post_json('/ticket/%s/transfer' % transfer_ticket['ticket_id'], dict({
        'user_email': receiver_user['email']
    }), headers=dict({
        "Authorization": "Bearer " + receiver_token
    }), status=403)

    # Transfer a ticket
    res = testapp.post_json('/ticket/%s/transfer' % transfer_ticket['ticket_id'], dict({
        'user_email': receiver_user['email']
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200)

    # Verify that the owner changed
    transferred_ticket = testapp.get('/ticket/%s' % transfer_ticket['ticket_id'], headers=dict({
        "Authorization": "Bearer " + receiver_token
    }), status=200).json_body
    assert transferred_ticket['owner']['uuid'] == receiver_user['uuid']

    # Verify that a ticket disappeared
    owned_tickets_post_transfer = testapp.get('/user/%s/owned_tickets' % sender_user['uuid'], headers=dict({
        "Authorization": "Bearer " + sender_token 
    }), status=200).json_body
    assert len(owned_tickets_post_transfer) < len(owned_tickets)

    # Check that the recipient received a ticket
    owned_tickets_recipient_post_transfer = testapp.get('/user/%s/owned_tickets' % receiver_user['uuid'], headers=dict({
        "Authorization": "Bearer " + receiver_token
    }), status=200).json_body

    assert len(owned_tickets_recipient_post_transfer) > len(owned_tickets_recipient)

    # Check that both people can see the ticket transfer, and assert it is not reversed and not expired
    sender_transfers = testapp.get('/user/%s/ticket_transfers?event_uuid=%s' % (sender_user['uuid'], upcoming_event.uuid), headers=dict({
        "Authorization": "Bearer " + sender_token,
    }), status=200).json_body

    assert len(sender_transfers) == 1

    receiver_transfers = testapp.get('/user/%s/ticket_transfers?event_uuid=%s' % (receiver_user['uuid'], upcoming_event.uuid), headers=dict({
        "Authorization": "Bearer " + receiver_token,
    }), status=200).json_body

    assert len(receiver_transfers) == 1

    assert receiver_transfers[0]['uuid'] == sender_transfers[0]['uuid']

    assert not sender_transfers[0]['expired']
    assert not sender_transfers[0]['reverted']

    # The receiver can't revert
    testapp.post_json('/ticket_transfer/%s/revert' % receiver_transfers[0]['uuid'], dict({
    }), headers=dict({
        "Authorization": "Bearer " + receiver_token
    }), status=403)

    # The receiver can't send the transfer to a third person
    res = testapp.post_json('/ticket/%s/transfer' % transfer_ticket['ticket_id'], dict({
        'user_email': receiver_2_user['email']
    }), headers=dict({
        "Authorization": "Bearer " + receiver_token
    }), status=400)

    # Revert the ticket transfer
    testapp.post_json('/ticket_transfer/%s/revert' % receiver_transfers[0]['uuid'], dict({
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200)

    # Check that the transfer isn't gone
    sender_transfers = testapp.get('/user/%s/ticket_transfers?event_uuid=%s' % (sender_user['uuid'], upcoming_event.uuid), headers=dict({
        "Authorization": "Bearer " + sender_token,
    }), status=200).json_body

    assert len(sender_transfers) == 1

    receiver_transfers = testapp.get('/user/%s/ticket_transfers?event_uuid=%s' % (receiver_user['uuid'], upcoming_event.uuid), headers=dict({
        "Authorization": "Bearer " + receiver_token,
    }), status=200).json_body

    assert len(receiver_transfers) == 1

    assert sender_transfers[0]['reverted']
    assert receiver_transfers[0]['reverted']

    # Make sure the owner has chagned back
    transferred_ticket = testapp.get('/ticket/%s' % transfer_ticket['ticket_id'], headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200).json_body
    assert transferred_ticket['owner']['uuid'] == sender_user['uuid']

    # You cannot revert something that is already reverted
    testapp.post_json('/ticket_transfer/%s/revert' % receiver_transfers[0]['uuid'], dict({
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=400)

