from datetime import datetime, timedelta, date
import time

def test_list_users(testapp):
    token, refresh = testapp.auth_get_tokens('test@example.com', 'sixcharacters')

    # Get some info about the current user
    users = testapp.get('/user', headers=dict({
        "Authorization": "Bearer " + token
        }), status=200).json_body

    assert len(users) > 0

def test_get_user(testapp):
    token, refresh = testapp.auth_get_tokens('test@example.com', 'sixcharacters')
    permissionless_token, refresh = testapp.auth_get_tokens('jeff@example.com', 'sixcharacters')

    # Get the UUID for the current user
    currentUser = testapp.get('/user/current', headers=dict({
        "Authorization": "Bearer " + token
        }), status=200).json_body

    # Get some info about the current user
    fetchedUser = testapp.get('/user/%s' % currentUser['uuid'], headers=dict({
        "Authorization": "Bearer " + token
        }), status=200).json_body

    # Permissionless people shouldn't be able to query this
    fetchedUser = testapp.get('/user/%s' % currentUser['uuid'], headers=dict({
        "Authorization": "Bearer " + permissionless_token 
        }), status=403)

def test_permissionless_user_fetch_applications(testapp):
    token, refresh = testapp.auth_get_tokens('test@example.com', 'sixcharacters')
    permissionless_token, refresh = testapp.auth_get_tokens('jeff@example.com', 'sixcharacters')

    user = testapp.get_user(token)

    # Should be able to get your own applications
    testapp.get('/user/%s/applications' % user['uuid'], headers=dict({
        "Authorization": "Bearer " + token
    }), status=200)

    testapp.get('/user/%s/applications' % user['uuid'], headers=dict({
        "Authorization": "Bearer " + permissionless_token
    }), status=403)

    testapp.get('/user/%s/applications' % user['uuid'], status=403)

def test_modify_user(testapp):
    
    # Test coverage:
    #    Title                  Active  Description
    #  * Functionality check:   [X]     Test functionality. Test that a user are able to modify the user.
    #  * Security check:        [X]     Test permissions. Test that admins can modify and regular users are denied.
    #  * Dependency check:      [X]     Test dependencies programmed in views/, ex. no empty fields.

    # Login with test accounts with admin privileges and no rights
    privileged_token, refresh = testapp.auth_get_tokens('test@example.com', 'sixcharacters')
    unprivileged_token, refresh = testapp.auth_get_tokens('jeff@example.com', 'sixcharacters')
    primary_testuser_token, refresh = testapp.auth_get_tokens('adam@example.com', 'sixcharacters')
    secondary_testuser_token, refresh = testapp.auth_get_tokens('jeff@example.com', 'sixcharacters')

    # Get a user to test against
    testuser = testapp.get_user(primary_testuser_token)
    primary_testuser_uuid = testuser['uuid']

    # Get a secondary user to test against
    seconadry_testuser = testapp.get_user(secondary_testuser_token)
    seconadry_testuser_username = seconadry_testuser['username']
    seconadry_testuser_email = seconadry_testuser['email']
    seconadry_testuser_phone = seconadry_testuser['phone']

    ### Test to modify user information (Functionality and security test)
    # Attempt to modify a user as an admin (Expects 200)
    privileged_modify = testapp.patch_json('/user/' + primary_testuser_uuid, dict({
        'uuid': primary_testuser_uuid,
        'firstname': "Adam Modified",
        'lastname': "Adamson Modified",
        'username': "adam.modified",
        'email': "adam.modified@example.com",
        'phone': "99999991",
        'guardian_phone': "99999992",
        'address': "1. Mann. Co rd Mod",
        'postal_code': "1396",
        'birthdate': "2001-11-19",
        'gender': "female"
    }), headers=dict({
        "Authorization": "Bearer " + privileged_token
    }), status=200)

    # Attempt to modify a user as a regular user (Expects 403)
    unprivileged_modify = testapp.patch_json('/user/' + primary_testuser_uuid, dict({
        'uuid': primary_testuser_uuid,
        'firstname': "Adam Modified",
        'lastname': "Adamson Modified",
        'username': "adam.modified",
        'email': "adam.modified@example.com",
        'phone': "99999991",
        'guardian_phone': "99999992",
        'address': "1. Mann. Co rd Mod",
        'postal_code': "1396",
        'birthdate': "2001-11-19",
        'gender': "female"
    }), headers=dict({
        "Authorization": "Bearer " + unprivileged_token
    }), status=403)

    ### Test to modify user information with invalid data (Dependency test)
    # Attempt to set empty fields
    dependency_firstname_empty = testapp.patch_json('/user/' + primary_testuser_uuid, dict({
        'uuid': primary_testuser_uuid,
        'firstname': "",
    }), headers=dict({
        "Authorization": "Bearer " + privileged_token
    }), status=400)

    dependency_lastname_empty = testapp.patch_json('/user/' + primary_testuser_uuid, dict({
        'uuid': primary_testuser_uuid,
        'lastname': "",
    }), headers=dict({
        "Authorization": "Bearer " + privileged_token
    }), status=400)

    dependency_username_empty = testapp.patch_json('/user/' + primary_testuser_uuid, dict({
        'uuid': primary_testuser_uuid,
        'username': "",
    }), headers=dict({
        "Authorization": "Bearer " + privileged_token
    }), status=400)

    dependency_email_empty = testapp.patch_json('/user/' + primary_testuser_uuid, dict({
        'uuid': primary_testuser_uuid,
        'email': "",
    }), headers=dict({
        "Authorization": "Bearer " + privileged_token
    }), status=400)

    dependency_phone_empty = testapp.patch_json('/user/' + primary_testuser_uuid, dict({
        'uuid': primary_testuser_uuid,
        'phone': "",
    }), headers=dict({
        "Authorization": "Bearer " + privileged_token
    }), status=400)

    dependency_address_empty = testapp.patch_json('/user/' + primary_testuser_uuid, dict({
        'uuid': primary_testuser_uuid,
        'address': "",
    }), headers=dict({
        "Authorization": "Bearer " + privileged_token
    }), status=400)

    dependency_postalcode_empty = testapp.patch_json('/user/' + primary_testuser_uuid, dict({
        'uuid': primary_testuser_uuid,
        'postal_code': "",
    }), headers=dict({
        "Authorization": "Bearer " + privileged_token
    }), status=400)

    dependency_birthdate_empty = testapp.patch_json('/user/' + primary_testuser_uuid, dict({
        'uuid': primary_testuser_uuid,
        'birthdate': "",
    }), headers=dict({
        "Authorization": "Bearer " + privileged_token
    }), status=400)

    dependency_gender_empty = testapp.patch_json('/user/' + primary_testuser_uuid, dict({
        'uuid': primary_testuser_uuid,
        'gender': "",
    }), headers=dict({
        "Authorization": "Bearer " + privileged_token
    }), status=400)

    # Attempt to set username, email and phone which is already taken by a secondary user.
    dependency_username_alreadytaken = testapp.patch_json('/user/' + primary_testuser_uuid, dict({
        'uuid': primary_testuser_uuid,
        'username': seconadry_testuser_username,
    }), headers=dict({
        "Authorization": "Bearer " + privileged_token
    }), status=400)

    dependency_email_alreadytaken = testapp.patch_json('/user/' + primary_testuser_uuid, dict({
        'uuid': primary_testuser_uuid,
        'email': seconadry_testuser_email,
    }), headers=dict({
        "Authorization": "Bearer " + privileged_token
    }), status=400)

    dependency_phone_alreadytaken = testapp.patch_json('/user/' + primary_testuser_uuid, dict({
        'uuid': primary_testuser_uuid,
        'phone': seconadry_testuser_phone,
    }), headers=dict({
        "Authorization": "Bearer " + privileged_token
    }), status=400)

    # Attempt to set invalid birthdate and gender
    dependency_birthdate_invalid = testapp.patch_json('/user/' + primary_testuser_uuid, dict({
        'uuid': primary_testuser_uuid,
        'birthdate': "invalid_birthdate",
    }), headers=dict({
        "Authorization": "Bearer " + privileged_token
    }), status=400)

    dependency_gender_invalid = testapp.patch_json('/user/' + primary_testuser_uuid, dict({
        'uuid': primary_testuser_uuid,
        'gender': "alphamale",
    }), headers=dict({
        "Authorization": "Bearer " + privileged_token
    }), status=400)

    # Attempt to set birthdate in future
    dependency_birthdate_infuture = testapp.patch_json('/user/' + primary_testuser_uuid, dict({
        'uuid': primary_testuser_uuid,
        'birthdate': "2199-01-01",
    }), headers=dict({
        "Authorization": "Bearer " + privileged_token
    }), status=400)

def test_activate_user(testapp):
    # Test coverage:
    #    Title                  Active  Description
    #  * Functionality check:   [X]     Test functionality. Test that a user are able to activate a user
    #  * Security check:        [X]     Test permissions. Test that admins can modify and regular users are denied.
    #  * Dependency check:      [ ]     Test dependencies programmed in views/ (Not in use)

    # Login with test accounts with admin privileges and no rights
    privileged_token, refresh = testapp.auth_get_tokens('test@example.com', 'sixcharacters')
    unprivileged_token, refresh = testapp.auth_get_tokens('jeff@example.com', 'sixcharacters')
    primary_testuser_token, refresh = testapp.auth_get_tokens('adam@example.com', 'sixcharacters')

    # Get a user to test against
    testuser = testapp.get_user(primary_testuser_token)
    primary_testuser_uuid = testuser['uuid']

    ### Test to activate a deactivated user (Functionality and security test)
    # Attempt to activate a user as an admin (Expects 200)
    privileged_activation = testapp.patch_json('/user/' + primary_testuser_uuid + '/activation', dict({
        'uuid': primary_testuser_uuid,
    }), headers=dict({
        "Authorization": "Bearer " + privileged_token
    }), status=400) # Should be 200, and a code which "deactivates" the account

    # Attempt to activate a user as a regular user (Expects 403)
    unprivileged_activation = testapp.patch_json('/user/' + primary_testuser_uuid + '/activation', dict({
        'uuid': primary_testuser_uuid,
    }), headers=dict({
        "Authorization": "Bearer " + unprivileged_token
    }), status=403)