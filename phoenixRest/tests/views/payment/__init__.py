from phoenixRest.tests.utils import initTestingDB, authenticate
from phoenixRest.tests.testCaseClass import TestCaseClass

from phoenixRest.features.payment.vipps import VIPPS_CALLBACK_AUTH_TOKEN

class FunctionalPaymentTests(TestCaseClass):
    def _get_user_uuid(self, token):
        res = self.testapp.get('/user/current', headers=dict({
            'X-Phoenix-Auth': token
        }), status=200)

        self.assertIsNotNone(res.json_body['uuid'])

        return res.json_body['uuid']
    
    def _create_store_session(self, token):
        res = self.testapp.get('/event/current', status=200)
        self.assertIsNotNone(res.json_body['uuid'])

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

        store_session = res.json_body['uuid']

        self.assertIsNotNone(store_session)
        return store_session

    # Test if we can create a payment
    def test_payment_flow_vipps(self):
        token, refresh = authenticate(self.testapp, 'test', 'sixcharacters')

        store_session = self._create_store_session(token)
        # Create a payment
        res = self.testapp.post_json('/payment', dict({
            'store_session': store_session,
            'provider': 'vipps'
        }), headers=dict({
            'X-Phoenix-Auth': token
        }), status=200)
        
        #self.assertIsNotNone(res.json_body['url'])
        #self.assertIsNotNone(res.json_body['slug'])
        #self.assertIsNotNone(res.json_body['payment_uuid'])
        self.assertIsNotNone(res.json_body['uuid'])

        payment_uuid = res.json_body['uuid']

        # Initiate the payment with vipps
        res = self.testapp.post_json('/payment/%s/initiate' % payment_uuid, dict({
            'fallback_url': "https://test.phoenix.no"
        }), headers=dict({
            'X-Phoenix-Auth': token
        }), status=200)
        self.assertIsNotNone(res.json_body['url'])
        self.assertIsNotNone(res.json_body['slug'])

        vipps_slug = res.json_body['slug']

        # Test that the ticket state is correct at this point
        res = self.testapp.get('/payment/%s' % payment_uuid,
            headers=dict({
                'X-Phoenix-Auth': token
            }),
            status=200)
        self.assertEquals(res.json_body['state'], "PaymentState.initiated")

        # Send the webhook
        # Test response payload from https://www.vipps.no/developers-documentation/ecom/documentation#callbacks
        res = self.testapp.post_json('/hooks/vipps/v2/payments/%s' % vipps_slug, dict({
            "merchantSerialNumber": 123456,
            "orderId": vipps_slug,
            "transactionInfo": {
                "amount": 20000,
                "status": "SALE",
                "timeStamp": "2018-12-12T11:18:38.246Z",
                "transactionId": "5001420062"
            }
        }), headers=dict({
            'Authorization': VIPPS_CALLBACK_AUTH_TOKEN
        }), status=200)

        # Tickets should now exist, so lets look for a ticket minted from this payment
        user_uuid = self._get_user_uuid(token)
        print("User uuid: %s" % user_uuid)
        
        res = self.testapp.get('/user/%s/purchased_tickets' % user_uuid, headers=dict({
            'X-Phoenix-Auth': token
        }))

        exists = False
        for ticket in res.json_body:
            if ticket['payment_uuid'] == payment_uuid:
                exists = True

        self.assertNotEquals(exists, False)
        # Ensure payments exists as well
        res = self.testapp.get('/user/%s/payments' % user_uuid, headers=dict({
            'X-Phoenix-Auth': token
        }))

        exists = False
        for payment in res.json_body:
            if payment['uuid'] == payment_uuid:
                exists = True

        self.assertNotEquals(exists, False)

        

    # Test if we can create a payment
    def test_payment_flow_stripe(self):
        token, refresh = authenticate(self.testapp, 'test', 'sixcharacters')

        store_session = self._create_store_session(token)
        # Create a payment
        res = self.testapp.post_json('/payment', dict({
            'store_session': store_session,
            'provider': 'stripe'
        }), headers=dict({
            'X-Phoenix-Auth': token
        }), status=200)
        
        self.assertIsNotNone(res.json_body['uuid'])

        payment_uuid = res.json_body['uuid']

        # Initiate the payment with vipps
        res = self.testapp.post_json('/payment/%s/initiate' % payment_uuid, dict({
            'fallback_url': "https://test.phoenix.no"
        }), headers=dict({
            'X-Phoenix-Auth': token
        }), status=200)
        self.assertIsNotNone(res.json_body['client_secret'])

        # Test that the ticket state is correct at this point
        res = self.testapp.get('/payment/%s' % payment_uuid,
            headers=dict({
                'X-Phoenix-Auth': token
            }),
            status=200)
        self.assertEquals(res.json_body['state'], "PaymentState.initiated")

        # TODO test webhook

        
