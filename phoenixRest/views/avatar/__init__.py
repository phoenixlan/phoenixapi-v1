from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow

from phoenixRest.models.core.avatar import Avatar, AvatarState

from phoenixRest.resource import resource

from phoenixRest.roles import ADMIN, CHIEF, HR_ADMIN

from phoenixRest.views.avatar.instance import AvatarInstanceResource

import logging
log = logging.getLogger(__name__)

@resource(name='avatar')
class AvatarResource(object):
    __acl__ = [
        (Allow, ADMIN, 'getAll'),
        (Allow, HR_ADMIN, 'getAll'),

        (Allow, ADMIN, 'getPending'),
        (Allow, HR_ADMIN, 'getPending'),
        (Allow, CHIEF, 'getPending'),

        # Authenticated pages
        #(Allow, Authenticated, Authenticated),
        #(Deny, Everyone, Authenticated),
    ]
    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        """Traverse to a specific crew item"""
        if key in ['pending']:
            raise KeyError('')
        node = AvatarInstanceResource(self.request, key)
        node.__parent__ = self
        node.__name__ = key
        return node

@view_config(context=AvatarResource, name='', request_method='GET', renderer='json', permission='getAll')
def get_all_avatars(request):
    # Returns all avatars
    return request.db.query(Avatar).order_by(Avatar.created).all()

@view_config(context=AvatarResource, name='pending', request_method='GET', renderer='json', permission='getPending')
def get_pending_avatars(request):
    # Returns all avatars
    return request.db.query(Avatar).filter(Avatar.state == AvatarState.uploaded).order_by(Avatar.created).all()
