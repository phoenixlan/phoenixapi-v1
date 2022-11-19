# Test listing crews, and make sure it works as intended both logged in as admin and not logged in
def test_login_doesnt_support_cors(testapp):
    # Do not support CORS for authentication
    testapp.options('/oauth/auth', status=404)

    # Support cors for other views
    testapp.options('/event/current', status=200)
