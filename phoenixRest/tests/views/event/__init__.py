from phoenixRest.tests.utils import initTestingDB, authenticate
from phoenixRest.tests.testCaseClass import TestCaseClass

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

        self.assertTrue(len(res.json_body) == 0)

        # Get ticket types
        ticket_types = self.testapp.get('/ticketType', headers=dict({
            'X-Phoenix-Auth': token
        }), status=200).json_body

        # Add a ticket type
        self.testapp.put_json('/event/%s/ticketType' % current_event.json_body['uuid'], dict({
            'ticket_type_uuid': ticket_types[0]['uuid']
        }), headers=dict({
            'X-Phoenix-Auth': token
        }), status=200)

        # The ticket type should now be added
        res = self.testapp.get('/event/%s/ticketType' % current_event.json_body['uuid'], headers=dict({
            'X-Phoenix-Auth': token
        }), status=200)

        self.assertTrue(len(res.json_body) == 1)


