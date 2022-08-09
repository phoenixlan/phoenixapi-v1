from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
)
from pyramid.security import Authenticated, Everyone, Deny, Allow


from phoenixRest.models import db
from phoenixRest.models.crew.position import Position

from phoenixRest.utils import validate
from phoenixRest.resource import resource

from phoenixRest.roles import ADMIN

from phoenixRest.views.position.instance import PositionInstanceResource

from datetime import datetime

import logging
log = logging.getLogger(__name__)


@resource(name='position')
class PositionResource(object):
    __acl__ = [
        (Allow, Everyone, 'getAll'),
        (Allow, ADMIN, 'create'),

        # Authenticated pages
        #(Allow, Authenticated, Authenticated),
        #(Deny, Everyone, Authenticated),
    ]
    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        node = PositionInstanceResource(self.request, key)
        node.__parent__ = self
        node.__name__ = key
        return node

@view_config(context=PositionResource, name='', request_method='GET', renderer='json', permission='getAll')
def get_all_positions(request):
    # Returns all avatars
    return db.query(Position).order_by(Position.name).all()

