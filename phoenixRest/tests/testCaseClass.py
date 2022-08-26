from phoenixRest.models import db

import unittest
class TestCaseClass(unittest.TestCase):
    def _get_user(self, token):
        res = self.testapp.get('/user/current', headers=dict({
            'X-Phoenix-Auth': token
        }), status=200)

        self.assertIsNotNone(res.json_body['uuid'])

        return res.json_body

    def setUp(self):
        from pyramid.paster import get_app
        app = get_app('paste_pytest.ini')
        from webtest import TestApp
        self.testapp = TestApp(app)

    def tearDown(self):
        # Won't really work
        db.rollback()