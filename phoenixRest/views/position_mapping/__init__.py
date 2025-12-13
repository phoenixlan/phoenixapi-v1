from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow

from sqlalchemy import and_

from phoenixRest.models.crew.position import Position

from phoenixRest.resource import resource

from phoenixRest.roles import ADMIN, MEMBER

from phoenixRest.models.core.user import User
from phoenixRest.models.core.event import Event
from phoenixRest.models.core.event import get_current_event
from phoenixRest.models.crew.position_mapping import PositionMapping

from phoenixRest.views.position_mapping.instance import PositionMappingInstanceResource

from phoenixRest.utils import validate

import logging
log = logging.getLogger(__name__)


@resource(name='position_mapping')
class PositionMappingResource(object):
    __acl__ = [
        (Allow, ADMIN, 'create_position_mapping'),
    ]
    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        node = PositionMappingInstanceResource(self.request, key)
        node.__parent__ = self
        node.__name__ = key
        return node

@view_config(context=PositionMappingResource, name='', request_method='POST', renderer='json', permission='create_position_mapping')
@validate(json_body={'user_uuid': str, 'position_uuid': str, 'event_uuid': str})
def create_mapping(context, request):
    user = request.db.query(User).filter(User.uuid == request.json_body['user_uuid']).first()
    if user is None:
        request.response.status = 404
        return {
            "error": "User not found"
        }
    
    position = request.db.query(Position) \
        .filter(Position.uuid == request.json_body['position_uuid']).first()
    
    if position is None:
        request.response.status = 404
        return {
            "error": "Position not found"
        }

    event = request.db.query(Event).filter(Event.uuid == request.json_body['event_uuid']).first()
    if event is None:
        request.response.status = 404
        return {
            "error": "Event not found"
        }
    
    existing_mapping = request.db.query(PositionMapping) \
        .filter(and_(
            PositionMapping.user == user,
            PositionMapping.event == event,
            PositionMapping.position == position
        )) \
        .first()

    if existing_mapping is not None:
        request.response.status = 400
        return {
            "error": "User already has a position mapping for the given position and event"
        }

    mapping = PositionMapping(user, position, event)

    position.position_mappings.append(mapping)
    request.db.add(mapping)
    request.db.flush()

    request.service_manager.get_service('position_notification').notify_user_position_mappings_changed(user)

    return mapping
