def upload_avatar_helper(testapp, username, password, path, x, y, w, h, expected_failure=None):
    token, refresh = testapp.auth_get_tokens(username, password)

    # Get some info about the current user
    currentUser = testapp.get('/user/current', headers=dict({
        "Authorization": "Bearer " + token
        }), status=200).json_body

    avatar_uuid = currentUser['avatar_uuid']
    user_uuid = currentUser['uuid']
    if avatar_uuid is not None:
        # Delete the avatar so we can test with a new one
        # This is done so the tests can run locally
        testapp.delete('/avatar/%s' % avatar_uuid, headers=dict({
            "Authorization": "Bearer " + token
            }), status=200)

    upload_res = testapp.post('/user/%s/avatar' % user_uuid, params="x=%d&y=%d&w=%d&h=%d"% (x, y, w, h), upload_files=[('file', path)], headers=dict({
        "Authorization": "Bearer " + token
    }), status = (expected_failure if expected_failure is not None else 200))

    if expected_failure is None:
        upload_res = upload_res.json_body
        # Try to delete it
        testapp.delete('/avatar/%s' % upload_res['uuid'], headers=dict({
            "Authorization": "Bearer " + token
        }), status=200)

def test_upload_avatar(testapp):
    # Log in as the test user
    upload_avatar_helper(testapp, 'test', 'sixcharacters', 'phoenixRest/tests/assets/avatar_test.png', 10, 10, 600, 450)

def test_upload_transparent_avatar(testapp):
    # Log in as the test user
    upload_avatar_helper(testapp, 'test', 'sixcharacters', 'phoenixRest/tests/assets/transparent.png', 10, 10, 600, 450)
    

def test_upload_avatar_bad_bounds(testapp):
    # Ensure the minimum requirements are held
    upload_avatar_helper(testapp, 'test', 'sixcharacters', 'phoenixRest/tests/assets/transparent.png', 10, 10, 10, 450, expected_failure=400)
    upload_avatar_helper(testapp, 'test', 'sixcharacters', 'phoenixRest/tests/assets/transparent.png', 10, 10, 600, 10, expected_failure=400)

    # Ensure that when the bounds are outside the image, the site complains
    upload_avatar_helper(testapp, 'test', 'sixcharacters', 'phoenixRest/tests/assets/transparent.png', 10, 10, 1000, 1000, expected_failure=400)

    # Ensure that when the bounding box starts outside the image, the site complains
    upload_avatar_helper(testapp, 'test', 'sixcharacters', 'phoenixRest/tests/assets/transparent.png', 1000, 1000, 600, 450, expected_failure=400)
    
