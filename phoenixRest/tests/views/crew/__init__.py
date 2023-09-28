# Test listing crews, and make sure it works as intended both logged in as admin and not logged in
def test_get_crews(testapp):
    res = testapp.get('/crew', status=200)
    assert len(res.json_body) > 0

    # Since the request is unauthenticated, make sure no inactive crews are visible
    hidden_crews = list(filter(lambda entry: entry['active'] == False, res.json_body))

    assert len(hidden_crews) == 0

    # Log in as the test user
    token, refresh = testapp.auth_get_tokens('test', 'sixcharacters')
    res = testapp.get('/crew', headers=dict({
        "Authorization": "Bearer " + token
        }), status=200)
    assert len(res.json_body) > 0

    # Make sure a hidden crew is visible now
    hidden_crews = list(filter(lambda entry: entry['active'] == False, res.json_body))

    assert len(hidden_crews) > 0
