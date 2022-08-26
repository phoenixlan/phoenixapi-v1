from phoenixRest.tests.utils import initTestingDB, authenticate
from phoenixRest.tests.testCaseClass import TestCaseClass

class FunctionalSecurityCorsTests(TestCaseClass):
    # Test listing crews, and make sure it works as intended both logged in as admin and not logged in
    def test_login_doesnt_support_cors(self):
        # Do not support CORS for authentication
        self.testapp.options('/oauth/auth', status=404)

        # Support cors for other views
        self.testapp.options('/event/current', status=200)
