from unittest import TestCase
from phoenixRest.tests.testCaseClass import TestCaseClass

"""
class ViewTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.session = _initTestingDB()

    def tearDown(self):
        testing.tearDown()

    def test_my_view(self):
        from .views import my_view
        request = testing.DummyRequest()
        info = my_view(request)
        self.assertEqual(info['user'], None)
"""

class FunctionalTests(TestCaseClass):
    def setUp(self):
        from pyramid.paster import get_app
        app = get_app('paste_pytest.ini')
        from webtest import TestApp
        self.testapp = TestApp(app)

# Test authentication with developer user
    def test_auth(self):
        res = self.testapp.post_json('/oauth/auth', dict({
            'login': 'test',
            'password': 'sixcharacters'
            }), status=200)
        self.assertTrue('code' in res.json_body)
        code = res.json_body['code']
        self.assertTrue(len(code) == 10)
        print("Testing with code: %s" % code)

        # Now try getting a token and refresh token
        res = self.testapp.post_json('/oauth/token', dict({
            'grant_type': 'code',
            'code': code
            }), status=200)

        self.assertTrue('token' in res.json_body)
        self.assertTrue('refresh_token' in res.json_body)

        refresh_token = res.json_body['refresh_token']
        # Can we refresh the token?
        res = self.testapp.post_json('/oauth/token', dict({
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
            }), status=200)

        self.assertTrue('token' in res.json_body)


# Test authentication with an invalid password
    def test_auth_bad(self):
        res = self.testapp.post_json('/oauth/auth', dict({
            'login': 'test',
            'password': 'bad'
            }), status=403)
