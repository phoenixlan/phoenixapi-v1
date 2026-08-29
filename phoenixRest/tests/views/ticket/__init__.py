
def test_ticket_creation_permissions(testapp, upcoming_event, ticket_types, admin_user, jeff_user):
    # test is an admin
    privileged_token, refresh = testapp.auth_get_tokens(admin_user.email, 'sixcharacters')
    unprivileged_token, refresh = testapp.auth_get_tokens(jeff_user.email, 'sixcharacters')

    # Get user UUID
    privileged_user = testapp.get_user(privileged_token)
    unprivileged_user = testapp.get_user(unprivileged_token)

    # Get existing ticket types
    res = testapp.get('/event/%s/ticketType' % upcoming_event.uuid, headers=dict({
        "Authorization": "Bearer " + privileged_token
    }), status=200)
    ticket_type = res.json_body[0]

    # Give test a free ticket. Only works because test is an admin
    res = testapp.post_json('/ticket', dict({
        'ticket_type': ticket_type['uuid'],
        'recipient': unprivileged_user['uuid'],
        'event_uuid': str(upcoming_event.uuid)
    }), headers=dict({
        "Authorization": "Bearer " + privileged_token
    }), status=200)

    # Now try with a non-authorized user. Should error.
    res = testapp.post_json('/ticket', dict({
        'ticket_type': ticket_type['uuid'],
        'recipient': unprivileged_user['uuid'],
        'event_uuid': str(upcoming_event.uuid)
    }), headers=dict({
        "Authorization": "Bearer " + unprivileged_token
    }), status=403)
