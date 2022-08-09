from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
)
from pyramid.security import Authenticated, Everyone, Deny, Allow


from phoenixRest.models import db
from phoenixRest.models.core.avatar import Avatar

from phoenixRest.utils import validate
from phoenixRest.resource import resource

from phoenixRest.roles import ADMIN, HR_ADMIN

from phoenixRest.views.avatar.instance import AvatarInstanceResource

from datetime import datetime

import logging
log = logging.getLogger(__name__)

@resource(name='avatar')
class AvatarResource(object):
    __acl__ = [
        (Allow, Everyone, 'get'),
        (Allow, ADMIN, 'getAll'),
        (Allow, HR_ADMIN, 'getAll'),

        # Authenticated pages
        #(Allow, Authenticated, Authenticated),
        #(Deny, Everyone, Authenticated),
    ]
    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        """Traverse to a specific crew item"""
        node = AvatarInstanceResource(self.request, key)
        node.__parent__ = self
        node.__name__ = key
        return node

@view_config(context=AvatarResource, name='', request_method='GET', renderer='json', permission='getAll')
def get_all_avatars(request):
    # Returns all avatars
    return db.query(Avatar).order_by(Avatar.created).all()
