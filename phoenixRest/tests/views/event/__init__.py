# Get ticket types for an event(we will use the current one)
def test_get_ticket_types(testapp, upcoming_event):
    token, refresh = testapp.auth_get_tokens('test@example.com', 'sixcharacters')

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


