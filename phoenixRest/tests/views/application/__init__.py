import unittest

from phoenixRest.tests.utils import initTestingDB, authenticate

from pyramid import testing

class FunctionalApplicationTests(unittest.TestCase):
    def setUp(self):
        from pyramid.paster import get_app
        app = get_app('paste_prod.ini')
        from webtest import TestApp
        self.testapp = TestApp(app)

    # Test listing crews, and make sure it works as intended both logged in as admin and not logged in
    def test_create_appliations(self):
        # Log in as the test user
        token, refresh = authenticate(self.testapp, 'test', 'sixcharacters')

        # We need the list of crews so we can apply for one
        crew_list = self.testapp.get('/crew', status=200).json_body

        res = self.testapp.put_json('/application', dict({
            'crew_uuid': crew_list[0]['uuid'],
            'contents': 'I want to join please'
        }), headers=dict({
            'X-Phoenix-Auth': token
        }), status=200)

        self.assertTrue(len(res.json_body) > 0)
