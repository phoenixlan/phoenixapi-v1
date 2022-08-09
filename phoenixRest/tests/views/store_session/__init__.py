import unittest

from phoenixRest.tests.utils import initTestingDB, authenticate

from pyramid import testing

class FunctionalStoreSessionTests(unittest.TestCase):
    def setUp(self):
        from pyramid.paster import get_app
        app = get_app('paste_prod.ini')
        from webtest import TestApp
        self.testapp = TestApp(app)

    # Test if we can reserve a store session
    def test_create_store_session(self):
        res = self.testapp.get('/event/current', status=200)
        self.assertIsNotNone(res.json_body['uuid'])

        token, refresh = authenticate(self.testapp, 'test', 'sixcharacters')

        res = self.testapp.get('/event/%s/ticketType' % res.json_body['uuid'], headers=dict({
            'X-Phoenix-Auth': token
        }), status=200)

        # Reserve a card for the first ticket for sale, i guess
        res = self.testapp.put_json('/store_session', dict({
            'cart': [
                {'qty': 1, 'uuid': res.json_body[0]['uuid']}
            ]
        }), headers=dict({
            'X-Phoenix-Auth': token
        }), status=200)

        self.assertIsNotNone(res.json_body['uuid'])

