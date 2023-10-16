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