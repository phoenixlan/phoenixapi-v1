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

def test_edit_event(testapp, upcoming_event):

    # Test coverage:
    #    Title                  Active  Description
    #  * Functionality check:   [X]     Test functionality. Test that a user are able to edit all event entries.
    #  * Security check:        [X]     Test permissions. Test that admins can edit and regular users cannot.
    #  * Dependency check:      [ ]     Test dependencies programmed in views/. (Not in use)

    # Get current event
    current_event = testapp.get('/event/current', status=200)
    assert current_event.json_body['uuid'] is not None

    # Login with test accounts with admin privileges and no rights
    privileged_token, refresh = testapp.auth_get_tokens('test@example.com', 'sixcharacters')
    unprivileged_token, refresh = testapp.auth_get_tokens('jeff@example.com', 'sixcharacters')

    # Get a seatmap
    seatmap = testapp.put_json('/seatmap', dict({
        'name': 'Test seatmap',
        'description': 'seatmap'
    }), headers=dict({
        "Authorization": "Bearer " + privileged_token
    }), status=200).json_body


    ### Test to edit an event as an admin (privileged) and as a regular user (unprivileged)
    # Attempt to edit an event as an admin (Expects 200)
    privileged_entry = testapp.patch_json('/event/%s/edit' % current_event.json_body['uuid'], dict({
        'name': "Edit name as admin",
        'start_time': 1896130800,
        'end_time': 1896303600,
        'booking_time': 1893452400,
        'priority_seating_time_delta': 200,
	    'seating_time_delta': 200,
	    'max_participants': 200,
	    'participant_age_limit_inclusive': 20,
	    'crew_age_limit_inclusive': 20,
	    'theme': "Edit theme as admin",
#       'location_uuid': X, // We do not have a "create location" code yet
        'seatmap_uuid': seatmap['uuid'],
        'cancellation_reason': "Edit cancellation reason as admin"
    }), headers=dict({
        "Authorization": "Bearer " + privileged_token
    }), status=200)

    # Attempt to create an event entry as a regular user (Expects 403)
    unprivileged_entry = testapp.patch_json('/event/%s/edit' % current_event.json_body['uuid'], dict({
        'name': "Edit event name as user",
        'start_time': 1896130403,
        'end_time': 1896303403,
        'booking_time': 1893452403,
        'priority_seating_time_delta': 403,
	    'seating_time_delta': 403,
	    'max_participants': 403,
	    'participant_age_limit_inclusive': 40,
	    'crew_age_limit_inclusive': 40,
	    'theme': "Edit theme as user",
#       'location_uuid': X, // We do not have a "create location" code yet
        'seatmap_uuid': seatmap['uuid'],
        'cancellation_reason': "Edit cancellation reason as user"
    }), headers=dict({
        "Authorization": "Bearer " + unprivileged_token
    }), status=403)

    # Attempt to read event entries where we expect all values to be updated
    assert privileged_entry.json_body['data']['name'] == "Edit name as admin"
    assert privileged_entry.json_body['data']['start_time'] == 1896130800
    assert privileged_entry.json_body['data']['end_time'] == 1896303600
    assert privileged_entry.json_body['data']['booking_time'] == 1893452400
    assert privileged_entry.json_body['data']['priority_seating_time_delta'] == 200
    assert privileged_entry.json_body['data']['seating_time_delta'] == 200
    assert privileged_entry.json_body['data']['max_participants'] == 200
    assert privileged_entry.json_body['data']['participant_age_limit_inclusive'] == 20
    assert privileged_entry.json_body['data']['crew_age_limit_inclusive'] == 20
    assert privileged_entry.json_body['data']['theme'] == "Edit theme as admin"
#   assert privileged_entry.json_body['data']['location_uuid'] == X // Not updated
    assert privileged_entry.json_body['data']['seatmap_uuid'] == seatmap['uuid']
    assert privileged_entry.json_body['data']['cancellation_reason'] == "Edit cancellation reason as admin"
