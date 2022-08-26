from phoenixRest.tests.utils import initTestingDB, authenticate
from phoenixRest.tests.testCaseClass import TestCaseClass

class FunctionalAvatarTests(TestCaseClass):
    # Test listing crews, and make sure it works as intended both logged in as admin and not logged in
    def test_list_avatars(self):
        # Log in as the test user
        token, refresh = authenticate(self.testapp, 'test', 'sixcharacters')

        res = self.testapp.get('/avatar', headers=dict({
            'X-Phoenix-Auth': token
        }), status=200)

