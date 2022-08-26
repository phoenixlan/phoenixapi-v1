from phoenixRest.tests.utils import initTestingDB, authenticate
from phoenixRest.tests.testCaseClass import TestCaseClass

class FunctionalTicketTransferTest(TestCaseClass):
    def test_ticket_transfer_flow(self):
        # test is an admin
        sender_token, refresh = authenticate(self.testapp, 'test', 'sixcharacters')
        receiver_token, refresh = authenticate(self.testapp, 'jeff', 'sixcharacters')
        receiver_2_token , refresh = authenticate(self.testapp, 'adam', 'sixcharacters')

        # Get user UUID
        sender_user = self._get_user(sender_token)
        receiver_user = self._get_user(receiver_token)
        receiver_2_user = self._get_user(receiver_2_token)

        # Current event
        current_event = self.testapp.get('/event/current', status=200)
        self.assertIsNotNone(current_event.json_body['uuid'])

        # Get existing ticket types
        res = self.testapp.get('/event/%s/ticketType' % current_event.json_body['uuid'], headers=dict({
            'X-Phoenix-Auth': sender_token
        }), status=200)
        ticket_type = res.json_body[0]

        # Give test a free ticket. Only works because test is an admin
        res = self.testapp.post_json('/ticket', dict({
            'ticket_type': ticket_type['uuid'],
            'recipient': sender_user['uuid']
        }), headers=dict({
            'X-Phoenix-Auth': sender_token
        }), status=200)

        # List the tickets owned by the test user
        owned_tickets = self.testapp.get('/user/%s/owned_tickets' % sender_user['uuid'], headers=dict({
            'X-Phoenix-Auth': sender_token 
        }), status=200).json_body
        self.assertGreater(len(owned_tickets), 0)

        # Get the tickets owned by the recipient prior to transfer
        owned_tickets_recipient = self.testapp.get('/user/%s/owned_tickets' % receiver_user['uuid'], headers=dict({
            'X-Phoenix-Auth': receiver_token
        }), status=200).json_body

        transfer_ticket = owned_tickets[0]

        # Someone who doesn't own a ticket can't transfer it
        res = self.testapp.post_json('/ticket/%s/transfer' % transfer_ticket['ticket_id'], dict({
            'user_email': receiver_user['email']
        }), headers=dict({
            'X-Phoenix-Auth': receiver_token
        }), status=403)

        # Transfer a ticket
        res = self.testapp.post_json('/ticket/%s/transfer' % transfer_ticket['ticket_id'], dict({
            'user_email': receiver_user['email']
        }), headers=dict({
            'X-Phoenix-Auth': sender_token
        }), status=200)

        # Verify that the owner changed
        transferred_ticket = self.testapp.get('/ticket/%s' % transfer_ticket['ticket_id'], headers=dict({
            'X-Phoenix-Auth': receiver_token
        }), status=200).json_body
        self.assertEqual(transferred_ticket['owner']['uuid'], receiver_user['uuid'])

        # Verify that a ticket disappeared
        owned_tickets_post_transfer = self.testapp.get('/user/%s/owned_tickets' % sender_user['uuid'], headers=dict({
            'X-Phoenix-Auth': sender_token 
        }), status=200).json_body
        self.assertLess(len(owned_tickets_post_transfer), len(owned_tickets))

        # Check that the recipient received a ticket
        owned_tickets_recipient_post_transfer = self.testapp.get('/user/%s/owned_tickets' % receiver_user['uuid'], headers=dict({
            'X-Phoenix-Auth': receiver_token
        }), status=200).json_body

        self.assertGreater(len(owned_tickets_recipient_post_transfer), len(owned_tickets_recipient))

        # Check that both people can see the ticket transfer, and assert it is not reversed and not expired
        sender_transfers = self.testapp.get('/user/%s/ticket_transfers' % sender_user['uuid'], headers=dict({
            'X-Phoenix-Auth': sender_token
        }), status=200).json_body

        self.assertEqual(len(sender_transfers), 1)

        receiver_transfers = self.testapp.get('/user/%s/ticket_transfers' % receiver_user['uuid'], headers=dict({
            'X-Phoenix-Auth': receiver_token
        }), status=200).json_body

        self.assertEqual(len(receiver_transfers), 1)

        self.assertEqual(receiver_transfers[0]['uuid'], sender_transfers[0]['uuid'])

        self.assertFalse(sender_transfers[0]['expired'])
        self.assertFalse(sender_transfers[0]['reverted'])

        # The receiver can't revert
        self.testapp.post_json('/ticket_transfer/%s/revert' % receiver_transfers[0]['uuid'], dict({
        }), headers=dict({
            'X-Phoenix-Auth': receiver_token
        }), status=403)

        # The receiver can't send the transfer to a third person
        res = self.testapp.post_json('/ticket/%s/transfer' % transfer_ticket['ticket_id'], dict({
            'user_email': receiver_2_user['email']
        }), headers=dict({
            'X-Phoenix-Auth': receiver_token
        }), status=400)

        # Revert the ticket transfer
        self.testapp.post_json('/ticket_transfer/%s/revert' % receiver_transfers[0]['uuid'], dict({
        }), headers=dict({
            'X-Phoenix-Auth': sender_token
        }), status=200)

        # Check that the transfer isn't gone
        sender_transfers = self.testapp.get('/user/%s/ticket_transfers' % sender_user['uuid'], headers=dict({
            'X-Phoenix-Auth': sender_token
        }), status=200).json_body

        self.assertEqual(len(sender_transfers), 1)

        receiver_transfers = self.testapp.get('/user/%s/ticket_transfers' % receiver_user['uuid'], headers=dict({
            'X-Phoenix-Auth': receiver_token
        }), status=200).json_body

        self.assertEqual(len(receiver_transfers), 1)

        self.assertTrue(sender_transfers[0]['reverted'])
        self.assertTrue(receiver_transfers[0]['reverted'])

        # Make sure the owner has chagned back
        transferred_ticket = self.testapp.get('/ticket/%s' % transfer_ticket['ticket_id'], headers=dict({
            'X-Phoenix-Auth': sender_token
        }), status=200).json_body
        self.assertEqual(transferred_ticket['owner']['uuid'], sender_user['uuid'])

        # You cannot revert something that is already reverted
        self.testapp.post_json('/ticket_transfer/%s/revert' % receiver_transfers[0]['uuid'], dict({
        }), headers=dict({
            'X-Phoenix-Auth': sender_token
        }), status=400)

    