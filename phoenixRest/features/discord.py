import os
import requests

DISCORD_CLIENT_ID = os.environ.get("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.environ.get("DISCORD_CLIENT_SECRET")
DISCORD_OAUTH_REDIRECT_URI = os.environ.get("DISCORD_OAUTH_REDIRECT_URI")

DISCORD_ENABLED = not (DISCORD_CLIENT_ID is None or DISCORD_OAUTH_REDIRECT_URI is None or DISCORD_CLIENT_SECRET is None)

DISCORD_API_ENDPOINT = "https://discord.com/api/v10"

DISCORD_SCOPES = '%20'.join(['identify', 'guilds.join'])

import logging
log = logging.getLogger(__name__)

def discord_exchange_code(code):
    data = {
        'client_id': DISCORD_CLIENT_ID,
        'client_secret': DISCORD_CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': DISCORD_OAUTH_REDIRECT_URI,
        'scope': DISCORD_SCOPES
    }
    log.info(data)
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    r = requests.post('%s/oauth2/token' % DISCORD_API_ENDPOINT, data=data, headers=headers)
    r.raise_for_status()
    return r.json()

def discord_refresh_tokens(refresh_token):
    data = {
        'client_id': DISCORD_CLIENT_ID,
        'client_secret': DISCORD_CLIENT_SECRET,
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    r = requests.post('%s/oauth2/token' % DISCORD_API_ENDPOINT, data=data, headers=headers)
    r.raise_for_status()
    return r.json()

def discord_get_bot_token():
    data = {
        'grant_type': 'client_credentials',
        'scope': 'identify'
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    r = requests.post('%s/oauth2/token' % DISCORD_API_ENDPOINT, data=data, headers=headers, auth=(DISCORD_CLIENT_ID, DISCORD_CLIENT_SECRET))
    r.raise_for_status()
    access_token = r.json()['access_token']
    return access_token

def discord_get_user(token):
    headers = {
        "Authorization": "Bearer %s" % token,
    }
    r = requests.get('%s/users/@me' % DISCORD_API_ENDPOINT, headers=headers)
    r.raise_for_status()
    user = r.json()
    return user

def discord_username_from_obj(user_obj):
    return "%s#%s" % (user_obj['username'], user_obj['discriminator'])
