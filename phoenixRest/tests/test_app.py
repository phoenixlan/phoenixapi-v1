import webtest

from datetime import datetime

import logging
log = logging.getLogger(__name__)

from phoenixRest.models.core.event import Event

class TestApp(webtest.TestApp):
    def auth_get_tokens(self, username, password):
        res = self.post_json('/oauth/auth', dict({
            'login': username,
            'password': password
            }), status=200)
        code = res.json_body['code']
        log.info("Authenticated, got code: %s" % code)

        # Now try getting a token and refresh token
        res = self.post('/oauth/token', {
                'grant_type': 'authorization_code',
                'code': code
            }, 
            headers = {'Content-Type': 'application/x-www-form-urlencoded'},
            status=200)

        return res.json_body['access_token'], res.json_body['refresh_token']
    
    def ensure_typical_event(self):
        token, refresh = self.auth_get_tokens('test', 'sixcharacters')

        current_event = self.get('/event/current', status=200).json_body

        # Add typical Ticket Types
        all_ticket_types = self.get('/ticketType', headers=dict({
            'Authorization': "Bearer " + token
        }), status=200).json_body

        for ticket_type in all_ticket_types:
            self.put_json('/event/%s/ticketType' % current_event['uuid'], dict({
                'ticket_type_uuid': ticket_type['uuid']
            }), headers=dict({
                'Authorization': "Bearer " + token
            }), status=200)
    
    def get_last_event(self, db):
        return db.query(Event) \
            .filter(Event.end_time < datetime.now()) \
            .order_by(Event.start_time.desc()).first()

    def get_current_event(self, db):
        return db.query(Event) \
            .filter(Event.end_time > datetime.now()) \
            .order_by(Event.start_time.asc()).first()

    def get_user(self, token):
        res = self.get('/user/current', headers=dict({
            'Authorization': "Bearer " + token
        }), status=200)

        return res.json_body