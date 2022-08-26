from phoenixRest.tests.utils import initTestingDB, authenticate
from phoenixRest.tests.testCaseClass import TestCaseClass

import json

class FunctionalTicketSeatingTest(TestCaseClass):
    def ensure_seatmap(self, token, event_uuid):
        event = self.testapp.get('/event/%s' % event_uuid, status=200).json_body
        if event['seatmap_uuid'] is not None:
            return
        
        seatmap = self.testapp.put_json('/seatmap', dict({
            'name': 'Test seatmap',
            'description': 'seatmap'
        }), headers=dict({
            'X-Phoenix-Auth': token
        }), status=200).json_body

        # Add a row
        row = self.testapp.put_json('/seatmap/%s/row' % seatmap['uuid'], dict({
            'row_number': 1,
            'x': 10,
            'y': 10,
            'horizontal': False
        }), headers=dict({
            'X-Phoenix-Auth': token
        }), status=200).json_body

        # Add three seats
        for i in range(0, 3):
            self.testapp.put_json('/row/%s/seat' % row['uuid'], dict({
            }), headers=dict({
                'X-Phoenix-Auth': token
            }), status=200).json_body

        # Re-fetch the seatmap
        seatmap = self.testapp.get('/seatmap/%s' % seatmap['uuid'], headers=dict({
            'X-Phoenix-Auth': token
        }), status=200).json_body

        return seatmap
    
    def ensure_ticket(self, token, event_uuid):
        # Get existing ticket types
        res = self.testapp.get('/event/%s/ticketType' % event_uuid, headers=dict({
            'X-Phoenix-Auth': token
        }), status=200)
        ticket_type = res.json_body[0]

        current_user = self._get_user(token)

        # Give test a free ticket. Only works because test is an admin
        res = self.testapp.post_json('/ticket', dict({
            'ticket_type': ticket_type['uuid'],
            'recipient': current_user['uuid']
        }), headers=dict({
            'X-Phoenix-Auth': token
        }), status=200)

        # List the tickets owned by the test user
        owned_tickets = self.testapp.get('/user/%s/owned_tickets' % current_user['uuid'], headers=dict({
            'X-Phoenix-Auth': token 
        }), status=200).json_body
        self.assertGreater(len(owned_tickets), 0)
        return owned_tickets[0]

    def test_ticket_seating(self):
        # test is an admin
        token, refresh = authenticate(self.testapp, 'test', 'sixcharacters')

        # Current event
        current_event = self.testapp.get('/event/current', status=200).json_body
        self.assertIsNotNone(current_event['uuid'])
        seatmap = self.ensure_seatmap(token, current_event['uuid'])

        seat_ticket = self.ensure_ticket(token, current_event['uuid'])

        availability = self.testapp.get('/seatmap/%s/availability' % seatmap['uuid'], headers=dict({
            'X-Phoenix-Auth': token
        }), status=200).json_body

        seat = None
        for row in availability['rows']:
            for seat_candidate in row['seats']:
                if seat_candidate['taken'] == False:
                    seat = seat_candidate
                    print(json.dumps(seat))
                    break
            else:
                continue
            break
            
        self.assertIsNotNone(seat)
        # Seat the ticket

        self.testapp.put_json('/ticket/%s/seat' % seat_ticket['ticket_id'], dict({
            'seat_uuid': seat['uuid']
        }), headers=dict({
            'X-Phoenix-Auth': token
        }), status=200)

        # Ensure the seatmap updated
        availability = self.testapp.get('/seatmap/%s/availability' % seatmap['uuid'], headers=dict({
            'X-Phoenix-Auth': token
        }), status=200).json_body

        asserted = False
        for row in availability['rows']:
            for seat_candidate in row['seats']:
                if seat_candidate['uuid'] == seat['uuid']:
                    self.assertTrue(seat_candidate['taken'])
                    asserted = True
            else:
                continue
            break
        self.assertTrue(asserted)

        # Ensure the ticket now has a seat
        ticket = self.testapp.get('/ticket/%s' % seat_ticket['ticket_id'], headers=dict({
            'X-Phoenix-Auth': token 
        }), status=200).json_body
        self.assertIsNotNone(ticket['seat'])
        self.assertEqual(ticket['seat']['uuid'], seat['uuid'])