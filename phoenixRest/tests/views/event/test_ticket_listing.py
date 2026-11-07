def test_event_ticket_listing(testapp, upcoming_event, ticket_types, admin_user, jeff_user):
    """Test that you can list tickets for an event"""
    privileged_token, refresh = testapp.auth_get_tokens(admin_user.email, 'sixcharacters')
    unprivileged_token, refresh = testapp.auth_get_tokens(jeff_user.email, 'sixcharacters')

    # Get user UUID
    privileged_user = testapp.get_user(privileged_token)
    unprivileged_user = testapp.get_user(unprivileged_token)

    # Test that the get tickets endpoint gives 0 tickets
    res = testapp.get('/event/%s/ticket' % upcoming_event.uuid, headers=dict({
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

    # Now there should be an entry
    res = testapp.get('/event/%s/ticket' % upcoming_event.uuid, headers=dict({
        "Authorization": "Bearer " + privileged_token
    }), status=200)
    assert len(res.json_body) == 1

def test_event_ticket_listing_as_ticket_audit(testapp, upcoming_event, ticket_types, greg_non_membership_ticket, ticket_audit_user):
    """Test that you can list tickets for an event with ticket audit permission"""
    privileged_token, refresh = testapp.auth_get_tokens(ticket_audit_user.email, 'sixcharacters')

    # Test ACL functionality for TICKET_AUDIT, check that the permission 'list' works.
    # The user should be able to read the ticket list, we expect status code 200, and get one ticket.
    res = testapp.get('/event/%s/ticket' % upcoming_event.uuid, headers=dict({
        "Authorization": "Bearer " + privileged_token
    }), status=200)
    assert len(res.json_body) == 1
    ticket = res.json_body[0]

    # Test ACL functionality for TICKET_AUDIT, check that the permission 'view_ticket' works.
    # The user should be able to view a ticket, we expect status code 200.
    res = testapp.get('/ticket/%s' % ticket['ticket_id'], headers=dict({
        "Authorization": "Bearer " + privileged_token
    }), status=200)
    assert res.json_body['ticket_id'] == ticket['ticket_id']

    # Test ACL functionality for TICKET_AUDIT, check that the permission 'ticket_type_mapping_list' works.
    # The user should be able to see which ticket types are mapped to an event, we expect status code 200
    res = testapp.get('/event/%s/ticket_type_mapping' % upcoming_event.uuid, headers=dict({
        "Authorization": "Bearer " + privileged_token
    }), status=200)

