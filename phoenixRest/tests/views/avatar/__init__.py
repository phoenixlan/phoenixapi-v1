import unittest

from phoenixRest.tests.utils import initTestingDB, authenticate

from pyramid import testing

class FunctionalAvatarTests(unittest.TestCase):
    def setUp(self):
        from pyramid.paster import get_app
        app = get_app('paste_prod.ini')
        from webtest import TestApp
        self.testapp = TestApp(app)

    # Test listing crews, and make sure it works as intended both logged in as admin and not logged in
    def test_list_avatars(self):
        # Log in as the test user
        token, refresh = authenticate(self.testapp, 'test', 'sixcharacters')

        res = self.testapp.get('/avatar', headers=dict({
            'X-Phoenix-Auth': token
        }), status=200)

