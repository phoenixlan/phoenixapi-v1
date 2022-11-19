def test_list_users(testapp):
    token, refresh = testapp.auth_get_tokens('test', 'sixcharacters')

    # Get some info about the current user
    users = testapp.get('/user', headers=dict({
        'X-Phoenix-Auth': token
        }), status=200).json_body

    assert len(users) > 0

def test_get_user(testapp):
    token, refresh = testapp.auth_get_tokens('test', 'sixcharacters')
    permissionless_token, refresh = testapp.auth_get_tokens('jeff', 'sixcharacters')

    # Get the UUID for the current user
    currentUser = testapp.get('/user/current', headers=dict({
        'X-Phoenix-Auth': token
        }), status=200).json_body

    # Get some info about the current user
    fetchedUser = testapp.get('/user/%s' % currentUser['uuid'], headers=dict({
        'X-Phoenix-Auth': token
        }), status=200).json_body

    # Permissionless people shouldn't be able to query this
    fetchedUser = testapp.get('/user/%s' % currentUser['uuid'], headers=dict({
        'X-Phoenix-Auth': permissionless_token 
        }), status=403)

