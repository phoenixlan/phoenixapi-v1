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
        token, refresh = self.auth_get_tokens('test@example.com', 'sixcharacters')

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
    
    def upload_avatar(self, email, password, path, x,y, w,h, expected_status=None):
        token, refresh = self.auth_get_tokens(email, password)
        
        # We get some info about the current user
        currentUser = self.get("/user/current/", headers=dict({
            "Authorization": "Bearer " + token
        }), status=200).json_body
        user_uuid = currentUser["uuid"]
        avatar_uuid = currentUser["avatar_uuid"]
        
        if avatar_uuid is not None:
            # Delete the avatar so we can test with a new one
            # This is done so the tests can run locally
            self.delete(f"/avatar/{avatar_uuid}/", headers=dict({
                "Authorization": "Bearer " + token
            }), status=200)
        
        upload_res = self.post(f"/user/{user_uuid}/avatar", params=f"x={x}&y={y}&w={w}&h={h}", upload_files=[("file", path)], headers=dict({
            "Authorization": "Bearer " + token
        }), status = (expected_status if expected_status is not None else 200))
        
        if expected_status is None:
            upload_res = upload_res.json_body
            # We try to delete the avatar
            self.delete("/avatar/%s" % upload_res["uuid"], headers=dict({
                "Authorization": "Bearer " + token
            }), status=200)
