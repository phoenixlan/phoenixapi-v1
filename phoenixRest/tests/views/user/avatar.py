from phoenixRest.tests.utils import initTestingDB, authenticate
from phoenixRest.tests.testCaseClass import TestCaseClass

class FunctionalUserAvatarTests(TestCaseClass):
    def setUp(self):
        from pyramid.paster import get_app
        app = get_app('paste_pytest.ini')
        from webtest import TestApp
        self.testapp = TestApp(app)

    def upload_avatar_helper(self, username, password, path, x, y, w, h, expected_failure=None):
        token, refresh = authenticate(self.testapp, username, password)

        # Get some info about the current user
        currentUser = self.testapp.get('/user/current', headers=dict({
            'X-Phoenix-Auth': token
            }), status=200).json_body

        avatar_uuid = currentUser['avatar_uuid']
        user_uuid = currentUser['uuid']
        if avatar_uuid is not None:
            # Delete the avatar so we can test with a new one
            # This is done so the tests can run locally
            self.testapp.delete('/avatar/%s' % avatar_uuid, headers=dict({
                'X-Phoenix-Auth': token
                }), status=200)

        upload_res = self.testapp.post('/user/%s/avatar' % user_uuid, params="x=%d&y=%d&w=%d&h=%d"% (x, y, w, h), upload_files=[('file', path)], headers=dict({
            'X-Phoenix-Auth': token
        }), status = (expected_failure if expected_failure is not None else 200))

        if expected_failure is None:
            upload_res = upload_res.json_body
            # Try to delete it
            self.testapp.delete('/avatar/%s' % upload_res['uuid'], headers=dict({
                'X-Phoenix-Auth': token
            }), status=200)

    def test_upload_avatar(self):
        # Log in as the test user
        self.upload_avatar_helper('test', 'sixcharacters', 'phoenixRest/tests/assets/avatar_test.png', 10, 10, 600, 450)

    def test_upload_transparent_avatar(self):
        # Log in as the test user
        self.upload_avatar_helper('test', 'sixcharacters', 'phoenixRest/tests/assets/transparent.png', 10, 10, 600, 450)
        

    def test_upload_avatar_bad_bounds(self):
        # Ensure the minimum requirements are held
        self.upload_avatar_helper('test', 'sixcharacters', 'phoenixRest/tests/assets/transparent.png', 10, 10, 10, 450, expected_failure=400)
        self.upload_avatar_helper('test', 'sixcharacters', 'phoenixRest/tests/assets/transparent.png', 10, 10, 600, 10, expected_failure=400)

        # Ensure that when the bounds are outside the image, the site complains
        self.upload_avatar_helper('test', 'sixcharacters', 'phoenixRest/tests/assets/transparent.png', 10, 10, 1000, 1000, expected_failure=400)

        # Ensure that when the bounding box starts outside the image, the site complains
        self.upload_avatar_helper('test', 'sixcharacters', 'phoenixRest/tests/assets/transparent.png', 1000, 1000, 600, 450, expected_failure=400)
        
