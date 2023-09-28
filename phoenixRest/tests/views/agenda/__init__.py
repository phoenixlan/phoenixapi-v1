import datetime
import time
import logging

# Test getting the current event
def test_get_agenda(testapp):
    return testapp.get('/agenda/', status=200)

def test_create_modify_delete_agenda(testapp):
    # Login with test accounts with admin privileges and no rights
    privileged_token, refresh = testapp.auth_get_tokens('test', 'sixcharacters')
    unprivileged_token, refresh = testapp.auth_get_tokens('jeff', 'sixcharacters')
    
    # Attempt to get current event
    current_event = testapp.get('/event/current', status=200)
    assert current_event.json_body['uuid'] is not None

    ### Test to create a new agenda entry as an admin (privileged) and as a regular user (unprivileged)
    # Attempt to create an agenda entry as an admin (Expects 200)
    privileged_entry = testapp.put_json('/agenda', dict({ 
        'event_uuid': current_event.json_body['uuid'],
        'title': "Test agenda entry as privileged",
        'description': "Test description",
        'location': "Test location",
        'time': int(datetime.datetime.now().timestamp()),
        'pinned': bool(False)
    }), headers=dict({
        "Authorization": "Bearer " + privileged_token
    }), status=200)

    # Attempt to create an agenda entry as a regular user (Expects 403)
    unprivileged_entry = testapp.put_json('/agenda', dict({ 
        'event_uuid': current_event.json_body['uuid'],
        'title': "Test agenda entry as unprivileged",
        'description': "Test description",
        'location': "Test location",
        'time': int(datetime.datetime.now().timestamp()),
        'pinned': bool(False)
    }), headers=dict({
        "Authorization": "Bearer " + unprivileged_token
    }), status=403)

    # Attempt to get the agenda entry uuid (Expects True)
    assert privileged_entry.json_body['uuid'] != None

    ### Test to modify a newly created agenda entry as an admin (privileged) and as a regular user (unprivileged)
    # Attempt to modify the newly created agenda entry as an admin, set everything (Expects 200)
    privileged_modification_setall = testapp.patch_json('/agenda/' + privileged_entry.json_body['uuid'], dict({ 
        'event_uuid': current_event.json_body['uuid'],
        'title': "Modified the title",
        'description': "Modified the description",
        'location': "Modified the location",
        'time': int(datetime.datetime.now().timestamp() + 692100),
        'deviating_time': int(datetime.datetime.now().timestamp()),
        'deviating_time_unknown': bool(True),
        'deviating_location': "Added deviating location",
        'deviating_information': "Added deviating information",
        'pinned': bool(True),
        'cancelled': bool(True)
    }), headers=dict({
        "Authorization": "Bearer " + privileged_token
    }), status=200)

    # Attempt to modify the newly created agenda entry as an admin, reset everything (Expects 200)
    privileged_modification_resetall = testapp.patch_json('/agenda/' + privileged_entry.json_body['uuid'], dict({ 
        'event_uuid': current_event.json_body['uuid'],
        'title': "Default title",
        'description': "Default description",
        'location': "Default location",
        'time': int(datetime.datetime.now().timestamp() + 692100),
        'deviating_time': None,
        'deviating_time_unknown': bool(False),
        'deviating_location': None,
        'deviating_information': None,
        'pinned': bool(False),
        'cancelled': bool(False)
    }), headers=dict({
        "Authorization": "Bearer " + privileged_token
    }), status=200)

    # Attempt to modify the newly created agenda entry as a regular user, set everything (Expects 403)
    unprivileged_modification_setall = testapp.patch_json('/agenda/' + privileged_entry.json_body['uuid'], dict({ 
        'event_uuid': current_event.json_body['uuid'],
        'title': "Modified the title a regular user",
        'description': "Modified the description",
        'location': "Modified the location",
        'time': int(datetime.datetime.now().timestamp() + 692100),
        'deviating_time': int(datetime.datetime.now().timestamp()),
        'deviating_time_unknown': bool(True),
        'deviating_location': "Added deviating location",
        'deviating_information': "Added deviating information",
        'pinned': bool(True),
        'cancelled': bool(True)
    }), headers=dict({
        "Authorization": "Bearer " + unprivileged_token
    }), status=403)

    ### Test to delete a newly created agenda entry as an admin (privileged) and as a regular user (unprivileged)
    # Attempt to delete the newly created agenda entry a regular user (Expects 403)
    unprivileged_deletion = testapp.delete('/agenda/' + privileged_entry.json_body['uuid'], headers=dict({
        "Authorization": "Bearer " + unprivileged_token 
    }), status=403)

    # Attempt to delete the newly created agenda entry as an admin (Expects 200)
    privileged_deletion = testapp.delete('/agenda/' + privileged_entry.json_body['uuid'], headers=dict({
        "Authorization": "Bearer " + privileged_token 
    }), status=200)

    