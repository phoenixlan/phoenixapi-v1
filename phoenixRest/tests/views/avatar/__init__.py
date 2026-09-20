# Test listing crews, and make sure it works as intended both logged in as admin and not logged in
def test_list_avatars(testapp, admin_user):
    # Log in as the test user
    token, refresh = testapp.auth_get_tokens(admin_user.email, 'sixcharacters')

    res = testapp.get('/avatar', headers=dict({
        "Authorization": "Bearer " + token
    }), status=200)
