import logging
log = logging.getLogger(__name__)

def test_get_ticket_transfer_log(testapp):
    
    # Test coverage:
    #    Title                  Active  Description
    #  * Functionality check:   [X]     Test functionality. Test that a user are able to read ticket transfer log and get a record
    #  * Security check:        [X]     Test permissions. Test that admins can read and regular users are denied.
    #  * Dependency check:      [X]     Test dependencies. Test that a ticket that does not exist returns not found.

    # Login with test accounts that are privileged and unprivileged
    privileged_token, refresh = testapp.auth_get_tokens('test@example.com', 'sixcharacters')
    unprivileged_sender_token, refresh = testapp.auth_get_tokens('jeff@example.com', 'sixcharacters')
    unprivileged_receiver_token, refresh = testapp.auth_get_tokens('adam@example.com', 'sixcharacters')

    unprivileged_sender_user = testapp.get_user(unprivileged_sender_token)
    unprivileged_receiver_user = testapp.get_user(unprivileged_receiver_token)

    # Current event
    current_event = testapp.get('/event/current', status=200)

    # Get existing ticket types
    res = testapp.get('/event/%s/ticketType' % current_event.json_body['uuid'], headers=dict({
        "Authorization": "Bearer " + privileged_token
    }), status=200)
    ticket_type = res.json_body[0]

    # Give test a free ticket. Only works because test is an admin
    new_ticket = testapp.post_json('/ticket', dict({
        'ticket_type': ticket_type['uuid'],
        'recipient': unprivileged_sender_user['uuid']
    }), headers=dict({
        "Authorization": "Bearer " + privileged_token
    }), status=200)

    # List the tickets owned by the test user
    owned_tickets = testapp.get('/user/%s/owned_tickets' % unprivileged_sender_user['uuid'], headers=dict({
        "Authorization": "Bearer " + unprivileged_sender_token 
    }), status=200).json_body

    transfer_ticket = owned_tickets[0]

    # Transfer a ticket to get a transfer record
    res = testapp.post_json('/ticket/%s/transfer' % transfer_ticket['ticket_id'], dict({
        'user_email': unprivileged_receiver_user['email']
    }), headers=dict({
        "Authorization": "Bearer " + unprivileged_sender_token
    }), status=200)

    

    # Test to read transfer log for a ticket as unprivileged user, expects 403 (Security check)
    transferlog_unprivileged = testapp.get('/ticket/%s/transfer_log' % transfer_ticket['ticket_id'], headers=dict({
        "Authorization": "Bearer " + unprivileged_sender_token
    }), status=403)

    # Test to read transfer log for a ticket as privileged user, expects 200 (Security check) and one log entry (Functionality check)
    transferlog_privileged = testapp.get('/ticket/%s/transfer_log' % transfer_ticket['ticket_id'], headers=dict({
        "Authorization": "Bearer " + privileged_token
    }), status=200).json_body
    assert len(transferlog_privileged) == 1

    # Test to read transfer log for a ticket that does not exist, expects 400 (Dependency check)
    transferlog_privileged_noticket = testapp.get('/ticket/0/transfer_log', headers=dict({
       "Authorization": "Bearer " + privileged_token
    }), status=404)
