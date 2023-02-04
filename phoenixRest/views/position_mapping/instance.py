from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPNotFound
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow

from phoenixRest.models.crew.position import Position 
from phoenixRest.models.crew.position_mapping import PositionMapping
from phoenixRest.models.core.user import User

from phoenixRest.mappers.position import map_position_with_position_mappings

from phoenixRest.roles import ADMIN, HR_ADMIN

from phoenixRest.utils import validate

import logging
log = logging.getLogger(__name__)


class PositionMappingInstanceResource(object):
    def __acl__(self):
        return [
            (Allow, ADMIN, 'delete_mapping'),
            (Allow, HR_ADMIN, 'delete_mapping'),
        ]

    def __init__(self, request, uuid):
        self.request = request
        self.positionMappingInstance = request.db.query(PositionMapping) \
            .filter(PositionMapping.uuid == uuid) \
            .first()

        if self.positionMappingInstance is None:
            raise HTTPNotFound("Position mapping not found")

@view_config(context=PositionMappingInstanceResource, request_method='DELETE', renderer='string', permission='delete_mapping')
def delete_position_mapping(context, request):
    request.db.delete(context.positionMappingInstance)
    return ""