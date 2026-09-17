# Test listing crews, and make sure it works as intended both logged in as admin and not logged in
def test_get_crews(testapp, db, testcrew, admin_user):
    res = testapp.get('/crew', status=200)
    assert len(res.json_body) > 0

    # Since the request is unauthenticated, make sure no inactive crews are visible
    hidden_crews = list(filter(lambda entry: entry['active'] == False, res.json_body))

    assert len(hidden_crews) == 0

    testcrew.active = False
    db.flush()

    # Log in as the test user
    token, refresh = testapp.auth_get_tokens(admin_user.email, 'sixcharacters')
    res = testapp.get('/crew', headers=dict({
        "Authorization": "Bearer " + token
        }), status=200)
    assert len(res.json_body) > 0

    # Make sure a hidden crew is visible now
    hidden_crews = list(filter(lambda entry: entry['active'] == False, res.json_body))

    assert len(hidden_crews) > 0


def test_get_crew_from_list_as_admin_and_member(
        testapp, testcrew, admin_user, greg_user):
    for user in [admin_user, greg_user]:
        token, refresh = testapp.auth_get_tokens(user.email, 'sixcharacters')
        headers = {
            "Authorization": "Bearer " + token
        }

        crews = testapp.get('/crew', headers=headers, status=200).json_body
        listed_crew = next(
            crew for crew in crews if crew['uuid'] == str(testcrew.uuid)
        )

        crew = testapp.get(
            '/crew/%s' % listed_crew['uuid'], headers=headers, status=200
        ).json_body
        assert crew['uuid'] == listed_crew['uuid']
