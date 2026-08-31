from datetime import datetime, timedelta


def _event_payload(name):
    start_time = datetime.now() + timedelta(days=100)
    return {
        'name': name,
        'start_time': int(start_time.timestamp()),
        'end_time': int((start_time + timedelta(days=3)).timestamp()),
        'max_participants': 500
    }


def test_create_event_for_brand_as_admin(testapp, event_brand, admin_token):
    event = testapp.put_json(
        '/event_brand/%s/event' % event_brand.uuid,
        _event_payload('Admin-created event'),
        headers={'Authorization': "Bearer " + admin_token},
        status=200
    ).json_body

    assert event['name'] == 'Admin-created event'
    assert event['event_brand_uuid'] == str(event_brand.uuid)
    assert event['max_participants'] == 500


def test_create_event_brand_admin_is_scoped(
        testapp, event_brand, other_event_brand, brand_admin_user):
    token, refresh = testapp.auth_get_tokens(
        brand_admin_user.email, 'sixcharacters'
    )
    headers = {'Authorization': "Bearer " + token}

    event = testapp.put_json(
        '/event_brand/%s/event' % event_brand.uuid,
        _event_payload('Brand-admin event'), headers=headers, status=200
    ).json_body
    assert event['event_brand_uuid'] == str(event_brand.uuid)

    testapp.put_json(
        '/event_brand/%s/event' % other_event_brand.uuid,
        _event_payload('Wrong-brand event'), headers=headers, status=403
    )


def test_create_event_rejects_permissionless_user(
        testapp, event_brand, adam_user):
    token, refresh = testapp.auth_get_tokens(adam_user.email, 'sixcharacters')
    testapp.put_json(
        '/event_brand/%s/event' % event_brand.uuid,
        _event_payload('Forbidden event'),
        headers={'Authorization': "Bearer " + token}, status=403
    )


# Get ticket types for an event(we will use the current one)
def test_get_ticket_types(testapp, upcoming_event, admin_user):
    token, refresh = testapp.auth_get_tokens(admin_user.email, 'sixcharacters')

    # Ensure there are ticket types. By default there aren't
    res = testapp.get('/event/%s/ticketType' % upcoming_event.uuid, headers=dict({
        "Authorization": "Bearer " + token
    }), status=200)

    assert len(res.json_body) == 0

    # Get ticket types
    ticket_types = testapp.get('/ticketType', headers=dict({
        "Authorization": "Bearer " + token
    }), status=200).json_body

    # Add a ticket type
    testapp.put_json('/event/%s/ticketType' % upcoming_event.uuid, dict({
        'ticket_type_uuid': ticket_types[0]['uuid']
    }), headers=dict({
        "Authorization": "Bearer " + token
    }), status=200)

    # The ticket type should now be added
    res = testapp.get('/event/%s/ticketType' % upcoming_event.uuid, headers=dict({
        "Authorization": "Bearer " + token
    }), status=200)

    assert len(res.json_body) == 1
