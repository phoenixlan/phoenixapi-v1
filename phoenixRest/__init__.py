import os
import uuid

import logging
log = logging.getLogger(__name__)

# Set up sentry
SENTRY_DSN = os.getenv('SENTRY_DSN', None)

if SENTRY_DSN is not None:
    log.info("Sentry DSN is provided - setting it up")
    import sentry_sdk

    from sentry_sdk.integrations.pyramid import PyramidIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[PyramidIntegration()]
    )
else:
    log.warning("WARNING: Sentry DSN is not provided")

JWT_SECRET = os.getenv('JWT_SECRET')

from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPOk
)

from pyramid.renderers import JSON
from pyramid.config import Configurator
from pyramid.events import NewRequest, NewResponse, subscriber
from pyramid.authorization import ACLAuthorizationPolicy

from phoenixRest.models import setup_session, setup_dbengine

from phoenixRest.models.core.user import User

from phoenixRest.resource import RootResource

from phoenixRest.features.mailProvider.mailgun import MailgunMailProvider
from phoenixRest.features.mailProvider import MailProvider

@subscriber(NewRequest)
def log_request(evt):
    log.info("%s %s" % (evt.request.method, evt.request.url))

@subscriber(NewResponse)
def set_cors(evt):
    """ Add CORS headers to the request """
    resp = evt.response
    resp.headers['Access-Control-Allow-Origin'] = "*"
    resp.headers['Access-Control-Allow-Headers'] = "Content-Type, X-Phoenix-Auth"
    resp.headers['Access-Control-Allow-Methods'] = "GET, POST, PUT, DELETE, " \
                                                   "PATCH"

@subscriber(NewRequest)
def verify_token(evt):
    """Force OPTIONS requests to succeed"""

    request = evt.request

    # Always allow CORS for paths handled by the API server.
    if request.method.upper() == "OPTIONS" and not request.path.startswith("/oauth/auth"):
        raise HTTPOk("CORS policy")


# This loads roles from the JWT claims and tells pyramid about them
def add_role_principals(userid, request):
    return ['role:%s' % role for role in request.jwt_claims.get('roles', [])]


def user(request):
    uuid = request.authenticated_userid
    log.info("Logged in as %s" % uuid)

    user = request.db.query(User).filter(User.uuid == uuid).first()
    if user is None:
        raise HTTPForbidden()
    return user

def get_root(request):
    return RootResource(request)

def uuid_adapter(obj, request):
    return str(obj)

def mail_provider(mailProvider: MailProvider):
    def inner(request):
        return mailProvider
    return inner

def main(global_config, dbengine=None, **settings):
    log.debug("Hello! The server is starting")

    if dbengine is None:
        log.debug("No dbengine provided, setting up my own")
        dbengine = setup_dbengine()

    db_session = setup_session(dbengine)

    config = Configurator(settings=settings, root_factory=RootResource)
    
    # Set up conversion of uuid to string
    json_renderer = JSON()
    json_renderer.add_adapter(uuid.UUID, uuid_adapter)
    config.add_renderer('json', json_renderer)

    # JWT
    config.set_authorization_policy(ACLAuthorizationPolicy())
    config.include('pyramid_jwt')
    config.set_jwt_authentication_policy(JWT_SECRET, http_header='X-Phoenix-Auth', expiration=60*60 if "DEBUG" in os.environ else 10*60, callback=add_role_principals)

    # Add a db connection handle to the request object
    def db(request):
        return db_session

    config.add_request_method(db, reify=True)

    # Add the user property to the request object
    config.add_request_method(user, reify=True)

    provider = MailProvider()
    
    log.info(settings)
    log.info(settings["service.mail.provider"])
    if "service.mail.provider" in settings:
        log.info("yes")
        if settings["service.mail.provider"] == "mailgun":
            log.info("mail")
            provider = MailgunMailProvider()
    
    config.add_request_method(mail_provider(provider), reify=True, name="mail_service")
    
    if "DEBUG" in os.environ:
        log.info("WARNING: Enabling debug")
        config.include("pyramid_debugtoolbar")

    config.include('pyramid_jinja2')

    # Event
    #config.add_route('event.current', '/event/current') # Placeholder
    #config.add_route('event', '/event')

    # Application
    #config.add_route('application.my', '/application/my') # Placeholder
    #config.add_route('application', '/application')

    log.debug('Start namespace scan')
    config.include('.routes')
    config.scan()

    log.debug("Done setting up the server")

    # config.scan('.views')
    return config.make_wsgi_app()
