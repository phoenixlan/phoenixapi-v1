import unittest

from phoenixRest.tests.utils import initTestingDB, authenticate

from pyramid import testing

class FunctionalEventTests(unittest.TestCase):
    def setUp(self):
        from pyramid.paster import get_app
        app = get_app('paste_prod.ini')
        from webtest import TestApp
        self.testapp = TestApp(app)

    # Test getting the current event
    def test_get_event(self):
        res = self.testapp.get('/event/current', status=200)
        self.assertIsNotNone(res.json_body['uuid'])

        token, refresh = authenticate(self.testapp, 'test', 'sixcharacters')

        res = self.testapp.get('/event/%s' % res.json_body['uuid'], headers=dict({
            'X-Phoenix-Auth': token
        }), status=200)
        self.assertIsNotNone(res)


    # Get ticket types for an event(we will use the current one)
    def test_get_ticket_types(self):
        res = self.testapp.get('/event/current', status=200)
        self.assertIsNotNone(res.json_body['uuid'])

        token, refresh = authenticate(self.testapp, 'test', 'sixcharacters')

        # Ensure there are ticket types. By default there aren't
        res = self.testapp.get('/event/%s/ticketType' % res.json_body['uuid'], headers=dict({
            'X-Phoenix-Auth': token
        }), status=200)

        self.assertTrue(len(res.json_body) > 0)

