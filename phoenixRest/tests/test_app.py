import webtest

import logging
log = logging.getLogger(__name__)

class TestApp(webtest.TestApp):
    def auth_get_tokens(self, username, password):
        res = self.post_json('/oauth/auth', dict({
            'login': username,
            'password': password
            }), status=200)
        code = res.json_body['code']
        log.info("Authenticated, got code: %s" % code)

        # Now try getting a token and refresh token
        res = self.post_json('/oauth/token', dict({
            'grant_type': 'code',
            'code': code
            }), status=200)

        return res.json_body['token'], res.json_body['refresh_token']
    
    def get_user(self, token):
        res = self.get('/user/current', headers=dict({
            'X-Phoenix-Auth': token
        }), status=200)

        return res.json_body