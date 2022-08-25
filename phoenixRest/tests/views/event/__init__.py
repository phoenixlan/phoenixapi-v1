from phoenixRest.tests.utils import initTestingDB, authenticate
from phoenixRest.tests.testCaseClass import TestCaseClass
import json
class FunctionalEventTests(TestCaseClass):
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
        current_event = self.testapp.get('/event/current', status=200)
        self.assertIsNotNone(current_event.json_body['uuid'])

        token, refresh = authenticate(self.testapp, 'test', 'sixcharacters')

        # Ensure there are ticket types. By default there aren't
        res = self.testapp.get('/event/%s/ticketType' % current_event.json_body['uuid'], headers=dict({
            'X-Phoenix-Auth': token
        }), status=200)
        print(json.dumps(res.json_body))

        # Relies on prior tests. TODO is to refactor db session creation
        self.assertTrue(len(res.json_body) > 0)


