from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPNotFound
)
from pyramid.security import Authenticated, Everyone, Deny, Allow

from phoenixRest.models import db
from phoenixRest.models.crew.position import Position 
from phoenixRest.models.crew.team import Team

from phoenixRest.roles import ADMIN

from phoenixRest.utils import validate
from phoenixRest.resource import resource

from datetime import datetime

import logging
log = logging.getLogger(__name__)


class PositionUserInstanceResource(object):
    def __acl__(self):
        return [
        (Allow, ADMIN, 'add_user'),
        (Allow, ADMIN, 'remove_user')
    ]


    def __init__(self, request):
        self.request = request


@view_config(context=PositionUserInstanceResource, name='', request_method='PUT', renderer='json', permission='add_to_position')
@validate(json_body={'uuid': str})
def add_to_position(context, request):
    user = db.query(User).filter(User.uuid == request.json_body['uuid']).first()
    if user is None:
        raise HTTPNotFound("User not found")

    self.__parent__.positionInstance.users.add(user)
    db.save(self.__parent__.positionInstance)
    return self.__parent__.positionInstance

    
@view_config(context=PositionUserInstanceResource, request_method='DELETE', renderer='json', permission='create_position')
def remove_from_position(context, request):
    
    raise HTTPNotFound("Not implemented")
