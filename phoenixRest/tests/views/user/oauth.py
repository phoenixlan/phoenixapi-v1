# Test authentication with developer user
def test_auth(testapp):
    res = testapp.post_json('/oauth/auth', dict({
        'login': 'test@example.com',
        'password': 'sixcharacters'
        }), status=200)
    assert 'code' in res.json_body
    code = res.json_body['code']
    assert len(code) == 20
    print("Testing with code: %s" % code)

    # Now try getting a token and refresh token
    res = testapp.post('/oauth/token', {
            'grant_type': 'authorization_code',
            'code': code
        },
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}, 
        status=200)

    assert 'access_token' in res.json_body
    assert 'refresh_token' in res.json_body

    refresh_token = res.json_body['refresh_token']
    # Can we refresh the token?
    res = testapp.post('/oauth/token', {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
        }, 
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}, 
        status=200)

    assert 'access_token' in res.json_body


# Test authentication with an invalid password
def test_auth_bad(testapp):
    testapp.post_json('/oauth/auth', dict({
        'login': 'test',
        'password': 'bad'
        }), status=403)
