from datetime import datetime

# Test getting the current event
def test_get_event(testapp, upcoming_event):
    res = testapp.get('/event/current', status=200)
    assert res.json_body['uuid'] is not None

    token, refresh = testapp.auth_get_tokens('test@example.com', 'sixcharacters')

    res = testapp.get('/event/%s' % res.json_body['uuid'], headers=dict({
        "Authorization": "Bearer " + token
    }), status=200)
    assert res is not None


# Get ticket types for an event(we will use the current one)
def test_get_ticket_types(testapp, upcoming_event):
    current_event = testapp.get('/event/current', status=200)
    assert current_event.json_body['uuid'] is not None

    token, refresh = testapp.auth_get_tokens('test@example.com', 'sixcharacters')

    # Ensure there are ticket types. By default there aren't
    res = testapp.get('/event/%s/ticketType' % current_event.json_body['uuid'], headers=dict({
        "Authorization": "Bearer " + token
    }), status=200)

    assert len(res.json_body) == 0

    # Get ticket types
    ticket_types = testapp.get('/ticketType', headers=dict({
        "Authorization": "Bearer " + token
    }), status=200).json_body

    # Add a ticket type
    testapp.put_json('/event/%s/ticketType' % current_event.json_body['uuid'], dict({
        'ticket_type_uuid': ticket_types[0]['uuid']
    }), headers=dict({
        "Authorization": "Bearer " + token
    }), status=200)

    # The ticket type should now be added
    res = testapp.get('/event/%s/ticketType' % current_event.json_body['uuid'], headers=dict({
        "Authorization": "Bearer " + token
    }), status=200)

    assert len(res.json_body) == 1

def test_create_event(testapp):

    # Test coverage:
    #    Title                  Active  Description
    #  * Functionality check:   [X]     Test functionality. Test that a user are able to create an event.
    #  * Security check:        [X]     Test permissions. Test that admins can create and regular users cannot.
    #  * Dependency check:      [ ]     Test dependencies programmed in views/. (Not in use)


    # Login with test accounts with admin privileges and no rights
    privileged_token, refresh = testapp.auth_get_tokens('test@example.com', 'sixcharacters')
    unprivileged_token, refresh = testapp.auth_get_tokens('jeff@example.com', 'sixcharacters')

    ### Test to create a new event entry as an admin (privileged) and as a regular user (unprivileged)
    # Attempt to create an event entry as an admin (Expects 200)
    privileged_entry = testapp.put_json('/event', dict({ 
        'name': "Privileged test event",
        'start_time': int(datetime.now().timestamp() + 172800),
        'end_time': int(datetime.now().timestamp() + 86400),
        'booking_time': int(datetime.now().timestamp()),
        'priority_seating_time_delta': 1800,
        'seating_time_delta': 3600,
        'max_participants': 200
    }), headers=dict({
        "Authorization": "Bearer " + privileged_token
    }), status=200)

    # Attempt to create an event entry as a regular user (Expects 403)
    unprivileged_entry = testapp.put_json('/event', dict({ 
        'name': "Unrivileged test event",
        'start_time': int(datetime.now().timestamp() + 172800),
        'end_time': int(datetime.now().timestamp() + 86400),
        'booking_time': int(datetime.now().timestamp()),
        'priority_seating_time_delta': 1800,
        'seating_time_delta': 3600,
        'max_participants': 403
    }), headers=dict({
        "Authorization": "Bearer " + unprivileged_token
    }), status=403)

    # Attempt to get the event entry uuid (Expects True)
    assert privileged_entry.json_body['uuid'] != None