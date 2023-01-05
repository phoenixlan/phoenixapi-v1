from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPNotFound
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow

from phoenixRest.models.crew.position import Position 
from phoenixRest.models.crew.position_mapping import PositionMapping
from phoenixRest.models.crew.team import Team
from phoenixRest.models.crew.crew import Crew
from phoenixRest.models.core.user import User

from phoenixRest.mappers.position import map_position_with_position_mappings

from phoenixRest.roles import ADMIN, HR_ADMIN

from phoenixRest.utils import validate

import logging
log = logging.getLogger(__name__)


class PositionInstanceResource(object):
    def __acl__(self):
        position_users = self.request.db.query(User).join(PositionMapping) \
            .filter(PositionMapping.position_uuid == self.positionInstance.uuid).all()

        return [
            (Allow, ADMIN, 'get_position'),
            (Allow, HR_ADMIN, 'get_position'),
            (Allow, ADMIN, 'create_position'),
            (Allow, HR_ADMIN, 'create_position'),

            (Allow, ADMIN, 'add_to_position'),
            (Allow, HR_ADMIN, 'add_to_position')
        # Everyone may look at their own
        ] + [(Allow, 'user:%s' % user.uuid, 'get_position') for user in position_users]

    def __init__(self, request, uuid):
        self.request = request
        self.positionInstance = request.db.query(Position).filter(Position.uuid == uuid).first()

        if self.positionInstance is None:
            raise HTTPNotFound("Position not found")

@view_config(context=PositionInstanceResource, name='', request_method='GET', renderer='json', permission='get_position')
def get_position(context, request):
    return map_position_with_position_mappings(context.positionInstance, request)
    
@view_config(context=PositionInstanceResource, name='', request_method='PUT', renderer='json', permission='create_position')
@validate(json_body={'name': str, 'description': str})
def create_position(context, request):
    position = Position(request.json_body['name'], request.json_body['description'])

    # Add crew
    if request.json_body['crew'] is not None:
        crew = request.db.query(Crew).filter(Crew.uuid == request.json_body['crew']).first()
        if crew is None:
            request.response.status = 404
            return {
                "error": "Crew not found"
            }
        position.crew = crew

    # Add team
    if request.json_body['team'] is not None:
        team = request.db.query(Team).filter(Team.uuid == request.json_body['team']).first()

        if team is None:
            request.response.status = 404
            return {
                "error": "Team not found"
            }

        position.team = team
    request.db.add(position)
    return position 
