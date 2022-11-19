# Test creating applications, and that the user is qualified to do so
def test_create_appliations(testapp):
    # Log in as the test user
    token, refresh = testapp.auth_get_tokens('test', 'sixcharacters')

    # Get the current user, ensure there is no avatar
    currentUser = testapp.get('/user/current', headers=dict({
        'X-Phoenix-Auth': token
        }), status=200).json_body

    avatar_uuid = currentUser['avatar_uuid']
    assert avatar_uuid is None

    # Upload an avatar
    testapp.post('/user/%s/avatar' % currentUser['uuid'], params="x=%d&y=%d&w=%d&h=%d"% (0, 0, 600, 450), upload_files=[('file', "phoenixRest/tests/assets/avatar_test.png")], headers=dict({
        'X-Phoenix-Auth': token
    }), status = 200)

    # We need the list of crews so we can apply for one
    crew_list = list(filter(lambda crew: crew["is_applyable"], testapp.get('/crew', status=200).json_body))

    res = testapp.put_json('/application', dict({
        'crew_uuid': crew_list[0]['uuid'],
        'contents': 'I want to join please'
    }), headers=dict({
        'X-Phoenix-Auth': token
    }), status=200)

    assert len(res.json_body) > 0
