from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPNotFound
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow

from phoenixRest.models.core.user import User

from phoenixRest.roles import ADMIN

from phoenixRest.utils import validate

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
    user = request.db.query(User).filter(User.uuid == request.json_body['uuid']).first()
    if user is None:
        request.response.status = 404
        return {
            "error": "User not found"
        }

    context.__parent__.positionInstance.users.add(user)
    request.db.save(context.__parent__.positionInstance)
    return context.__parent__.positionInstance

    
@view_config(context=PositionUserInstanceResource, request_method='DELETE', renderer='json', permission='create_position')
def remove_from_position(context, request):
    
    raise HTTPNotFound("Not implemented")
