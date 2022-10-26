# Test listing crews, and make sure it works as intended both logged in as admin and not logged in
def test_list_avatars(testapp):
    # Log in as the test user
    token, refresh = testapp.auth_get_tokens('test', 'sixcharacters')

    res = testapp.get('/avatar', headers=dict({
        'X-Phoenix-Auth': token
    }), status=200)

