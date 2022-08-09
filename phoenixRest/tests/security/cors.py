import unittest

from phoenixRest.tests.utils import initTestingDB, authenticate

from pyramid import testing

class FunctionalSecurityCorsTests(unittest.TestCase):
    def setUp(self):
        from pyramid.paster import get_app
        app = get_app('paste_prod.ini')
        from webtest import TestApp
        self.testapp = TestApp(app)

    # Test listing crews, and make sure it works as intended both logged in as admin and not logged in
    def test_login_doesnt_support_cors(self):
        # Do not support CORS for authentication
        self.testapp.options('/oauth/auth', status=404)

        # Support cors for other views
        self.testapp.options('/event/current', status=200)
