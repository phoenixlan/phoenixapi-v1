
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
    res = testapp.post_json('/event/%s/ticket' % upcoming_event.uuid, dict({
        'ticket_type': ticket_type['uuid'],
        'recipient': unprivileged_user['uuid']
    }), headers=dict({
        "Authorization": "Bearer " + privileged_token
    }), status=200)

    # Now try with a non-authorized user. Should error.
    res = testapp.post_json('/event/%s/ticket' % upcoming_event.uuid, dict({
        'ticket_type': ticket_type['uuid'],
        'recipient': unprivileged_user['uuid']
    }), headers=dict({
        "Authorization": "Bearer " + unprivileged_token
    }), status=403)

def test_ticket_admin_is_scoped_to_event_brand(
        testapp, upcoming_event, other_upcoming_event, ticket_types,
        ticket_admin_user, jeff_user):
    token, refresh = testapp.auth_get_tokens(
        ticket_admin_user.email, 'sixcharacters'
    )
    ticket_type = testapp.get(
        '/event/%s/ticketType' % upcoming_event.uuid, status=200
    ).json_body[0]

    testapp.post_json('/event/%s/ticket' % upcoming_event.uuid, {
        'ticket_type': ticket_type['uuid'],
        'recipient': str(jeff_user.uuid)
    }, headers={
        'Authorization': "Bearer " + token
    }, status=200)

    testapp.post_json('/event/%s/ticket' % other_upcoming_event.uuid, {
        'ticket_type': ticket_type['uuid'],
        'recipient': str(jeff_user.uuid)
    }, headers={
        'Authorization': "Bearer " + token
    }, status=403)

def test_ticket_rejects_ticket_type_from_other_brand(
        testapp, upcoming_event, other_ticket_type, admin_token, jeff_user):
    response = testapp.post_json('/event/%s/ticket' % upcoming_event.uuid, {
        'ticket_type': str(other_ticket_type.uuid),
        'recipient': str(jeff_user.uuid)
    }, headers={
        'Authorization': "Bearer " + admin_token
    }, status=400)

    assert response.json_body['error'] == \
        'Ticket type belongs to a different event brand'
