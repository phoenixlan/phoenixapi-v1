import unittest

from phoenixRest.tests.utils import initTestingDB, authenticate

from pyramid import testing

class FunctionalUserTests(unittest.TestCase):
    def setUp(self):
        from pyramid.paster import get_app
        app = get_app('paste_prod.ini')
        from webtest import TestApp
        self.testapp = TestApp(app)

    def test_list_users(self):
        token, refresh = authenticate(self.testapp, 'test', 'sixcharacters')

        # Get some info about the current user
        currentUser = self.testapp.get('/user', headers=dict({
            'X-Phoenix-Auth': token
            }), status=200).json_body

        self.assertTrue(len(currentUser) > 0)

    def test_get_user(self):
        token, refresh = authenticate(self.testapp, 'test', 'sixcharacters')

        # Get the UUID for the current user
        currentUser = self.testapp.get('/user/current', headers=dict({
            'X-Phoenix-Auth': token
            }), status=200).json_body

        # Get some info about the current user
        fetchedUser = self.testapp.get('/user/%s' % currentUser['uuid'], headers=dict({
            'X-Phoenix-Auth': token
            }), status=200).json_body

