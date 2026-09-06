from pyramid.authorization import Allow
from pyramid.view import view_config
from sqlalchemy import and_

from phoenixRest.models.core.user import User
from phoenixRest.models.crew.position import Position
from phoenixRest.models.crew.position_mapping import PositionMapping
from phoenixRest.roles import ADMIN, HR_ADMIN
from phoenixRest.utils import validate


class EventPositionMappingResource(object):
    def __acl__(self):
        return [
            (Allow, ADMIN(), 'create_position_mapping'),
            (Allow, HR_ADMIN(self.event.event_brand_uuid), 'create_position_mapping')
        ]

    def __init__(self, request, event):
        self.request = request
        self.event = event


@view_config(context=EventPositionMappingResource, request_method='POST', renderer='json', permission='create_position_mapping')
@validate(json_body={'user_uuid': str, 'position_uuid': str})
def create_mapping(context, request):
    user = request.db.query(User).filter(User.uuid == request.json_body['user_uuid']).first()
    if user is None:
        request.response.status = 404
        return {
            "error": "User not found"
        }

    position = request.db.query(Position) \
        .filter(Position.uuid == request.json_body['position_uuid']) \
        .first()
    if position is None:
        request.response.status = 404
        return {
            "error": "Position not found"
        }

    if position.event_brand_uuid != context.event.event_brand_uuid:
        request.response.status = 400
        return {
            "error": "Position belongs to a different event brand"
        }

    existing_mapping = request.db.query(PositionMapping) \
        .filter(and_(
            PositionMapping.user == user,
            PositionMapping.event == context.event,
            PositionMapping.position == position
        )) \
        .first()

    if existing_mapping is not None:
        request.response.status = 400
        return {
            "error": "User already has a position mapping for the given position and event"
        }

    mapping = PositionMapping(user, position, context.event)
    position.position_mappings.append(mapping)
    request.db.add(mapping)
    request.db.flush()

    request.service_manager.get_service('position_notification') \
        .notify_user_position_mappings_changed(user)

    return mapping
