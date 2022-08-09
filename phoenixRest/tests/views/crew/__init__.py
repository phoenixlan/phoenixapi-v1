import unittest

from phoenixRest.tests.utils import initTestingDB, authenticate

from pyramid import testing

class FunctionalCrewTests(unittest.TestCase):
    def setUp(self):
        from pyramid.paster import get_app
        app = get_app('paste_prod.ini')
        from webtest import TestApp
        self.testapp = TestApp(app)

    # Test listing crews, and make sure it works as intended both logged in as admin and not logged in
    def test_get_crews(self):
        res = self.testapp.get('/crew', status=200)
        self.assertTrue(len(res.json_body) > 0)

        # Since the request is unauthenticated, make sure no inactive crews are visible
        hidden_crews = list(filter(lambda entry: entry['active'] == False, res.json_body))

        self.assertTrue(len(hidden_crews) == 0)

        # Log in as the test user
        token, refresh = authenticate(self.testapp, 'test', 'sixcharacters')
        res = self.testapp.get('/crew', headers=dict({
            'X-Phoenix-Auth': token
            }), status=200)
        self.assertTrue(len(res.json_body) > 0)

        # Make sure a hidden crew is visible now
        hidden_crews = list(filter(lambda entry: entry['active'] == False, res.json_body))

        self.assertTrue(len(hidden_crews) > 0)
