from pyramid.view import view_config
from pyramid.authorization import Allow


from phoenixRest.models.tickets.store_session import StoreSession
from phoenixRest.resource import resource

from phoenixRest.roles import ADMIN

from datetime import datetime

import logging
log = logging.getLogger(__name__)

@resource(name='store_session')
class StoreSessionResource(object):
    __acl__ = [
        (Allow, ADMIN(), 'fetch_all'),

        (Allow, ADMIN(), 'fetch_active'),

        # Authenticated pages
        #(Allow, Authenticated, Authenticated),
        #(Deny, Everyone, Authenticated),
    ]
    def __init__(self, request):
        self.request = request


@view_config(context=StoreSessionResource, name='', request_method='GET', renderer='json', permission='fetch_all')
def get_all_sessions(request):
    # Returns all active store sessions
    return request.db.query(StoreSession).order_by(StoreSession.created).all()

@view_config(context=StoreSessionResource, name='active', request_method='GET', renderer='json', permission='fetch_active')
def get_active_sessions(request):
    # Returns all active store sessions
    return request.db.query(StoreSession).filter(StoreSession.expires > datetime.now()).order_by(StoreSession.created).all()
