import transaction

def test_all_ticket_listing(testapp, upcoming_event, ticket_types, admin_user, jeff_user):
    """Test that you can list tickets.
    Probably never used"""
    privileged_token, refresh = testapp.auth_get_tokens(admin_user.email, 'sixcharacters')
    unprivileged_token, refresh = testapp.auth_get_tokens(jeff_user.email, 'sixcharacters')

    # Get user UUID
    privileged_user = testapp.get_user(privileged_token)
    unprivileged_user = testapp.get_user(unprivileged_token)

    # Test that the get tickets endpoint gives 0 tickets
    res = testapp.get('/ticket', headers=dict({
        "Authorization": "Bearer " + privileged_token
    }), status=200)
    assert len(res.json_body) == 0

    # Get existing ticket types
    res = testapp.get('/event/%s/ticketType' % upcoming_event.uuid, headers=dict({
        "Authorization": "Bearer " + privileged_token
    }), status=200)
    ticket_type = res.json_body[0]

    # Give test a free ticket. Only works because test is an admin
    res = testapp.post_json('/event/%s/ticket' % upcoming_event.uuid, dict({
        'ticket_type': ticket_type['uuid'],
        'recipient': unprivileged_user['uuid']
    }), headers=dict({
        "Authorization": "Bearer " + privileged_token
    }), status=200)

    transaction.commit()

    # Now there should be an entry
    res = testapp.get('/ticket', headers=dict({
        "Authorization": "Bearer " + privileged_token
    }), status=200)
    assert len(res.json_body) == 1
