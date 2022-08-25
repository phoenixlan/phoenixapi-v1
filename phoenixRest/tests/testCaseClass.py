from phoenixRest.models import db

import unittest
class TestCaseClass(unittest.TestCase):
    def setUp(self):
        from pyramid.paster import get_app
        app = get_app('paste_pytest.ini')
        from webtest import TestApp
        self.testapp = TestApp(app)

    def tearDown(self):
        # Won't really work
        db.rollback()