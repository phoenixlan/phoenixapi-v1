from datetime import datetime, timedelta
import requests
import json
import os

from phoenixRest.models.tickets.payment_providers.vipps_payment import VippsPayment
from phoenixRest.models.tickets.payment import Payment
from phoenixRest.models import db

from phoenixRest.features.payment import mint_tickets

import logging
log = logging.getLogger(__name__)

CLIENT_ID = os.environ["VIPPS_CLIENT_ID"]
CLIENT_SECRET = os.environ["VIPPS_CLIENT_SECRET"]
SUBSCRIPTION_KEY =os.environ["VIPPS_SUBSCRIPTION_KEY"]

# Used during callbacks so vipps can authenticate
VIPPS_CALLBACK_AUTH_TOKEN = os.environ.get("VIPPS_CALLBACK_AUTH_TOKEN", "62f87f5f26c34caa18589d244ce49670680050faad9d48a1322d2bf8af6f883a")

API_ROOT = os.environ.get("VIPPS_API_ROOT", "https://apitest.vipps.no")

# Static values
MERCHANT_SERIAL_NUMBER = os.environ["VIPPS_MERCHANT_SERIAL_NUMBER"] #If we get more units we can change this
VIPPS_SYSTEM_VERSION = "0.1"
VIPPS_SYSTEM_NAME = "PhonixRest"
CALLBACK_PREFIX = os.environ["VIPPS_CALLBACK_URL"]

token = None
nextTokenFetchTime = datetime.now()

"""
TODO The following extra headers should probably be sent

Merchant-Serial-Number
Vipps-System-Name
Vipps-System-Version
Vipps-System-Plugin-Name
Vipps-System-Plugin-Version

See https://github.com/vippsas/vipps-ecom-api/blob/master/vipps-ecom-api.md#optional-vipps-http-headers
"""

def _get_headers():
	return {
		"Ocp-Apim-Subscription-Key": SUBSCRIPTION_KEY,
		# Vipps wants this to be sent
		"Merchant-Serial-Number": MERCHANT_SERIAL_NUMBER,
		"Vipps-System-Version": VIPPS_SYSTEM_VERSION,
		"Vipps-System-Name": VIPPS_SYSTEM_NAME
	}

def _fetchToken():
	global token
	global nextTokenFetchTime
	response = requests.post('%s/accesstoken/get' % API_ROOT,
				headers={
					**_get_headers(), 
					**{
						"client_id": CLIENT_ID,
						"client_secret": CLIENT_SECRET
					}})
	log.debug('Access token response: %d' % response.status_code)
	tokenMetadata = response.json()
	log.debug(tokenMetadata)

	token = tokenMetadata["access_token"]
	# Subtract 2 to compensate for network lag?
	nextTokenFetchTime = datetime.fromtimestamp(int(tokenMetadata['expires_on'])-2)

	log.debug('Next token fetch in %s seconds' % tokenMetadata["expires_in"])

def _ensureToken():
	global token
	global nextTokenFetchTime

	if token is None or nextTokenFetchTime < datetime.now():
		_fetchToken()
	else:
		log.debug("Token is already fetched")

def _initiatePayment(payment, vipps_payment, fallback):
	global token

	paymentStr = ", ".join(["%s %s-billett%s" % (entry.amount, entry.ticket_type.name, "er" if entry.amount > 1 else "") for entry in payment.store_session.cart_entries])

	payload = {
		"customerInfo": {
			"mobileNumber": payment.user.phone
		},
		"merchantInfo": {
			"authToken": VIPPS_CALLBACK_AUTH_TOKEN,
			"merchantSerialNumber": MERCHANT_SERIAL_NUMBER,
			"callbackPrefix": CALLBACK_PREFIX,
			"fallBack": fallback,
			"isApp": False
		},
		"transaction": {
			"orderId": vipps_payment.slug,
			"amount": payment.price*100,
			"transactionText": paymentStr,
		}
	}

	log.debug("Sending %s" % json.dumps(payload))

	response = requests.post('%s/ecomm/v2/payments' % API_ROOT,
				headers={
					**_get_headers(), 
					**{
						"Authorization": token,
						"Content-Type": "application/json"
					}},
				json=payload)
	log.debug('Initiate payment response: %d' % response.status_code)

	paymentMetadata = response.json()
	log.debug(paymentMetadata)

	#vippsOrderId = tokenMetadata['orderId']

	if response.status_code != 200:
		return None
	
	vipps_payment.order_id = paymentMetadata['orderId']
	db.add(vipps_payment)

	return paymentMetadata['url']

def _cancelOrder(self):
	pass

def _mock_vipps():
	return "https://api.test.phoenix.no/vippsDeeplinkPlaceholder"

def initialize_vipps_payment(payment: Payment, fallback_url: str):
	# Don't talk to vipps if we are running tests
	if not "PYTEST_CURRENT_TEST" in os.environ:
		_ensureToken()

	if not payment.store_session:
		raise RuntimeError('Tried to initiate vipps on a payment without store session')

	vippsPayment = VippsPayment(payment)
	db.add(vippsPayment)

	if not "PYTEST_CURRENT_TEST" in os.environ:
		deeplinkUrl = _initiatePayment(payment, vippsPayment, fallback_url)
	else:
		deeplinkUrl = _mock_vipps()

	if deeplinkUrl:
		# Update the expiry. Vipps payments expire after 10 mins
		# TODO find a source for this information
		payment.store_session.expires = datetime.now() + timedelta(minutes=10)
		db.add(payment)
		# Return a payment ID
		return deeplinkUrl, vippsPayment.slug
	return None, None

def finalize_vipps_payment(request, payment: VippsPayment):
    # Mint tickets
    mint_tickets(request, payment.payment)