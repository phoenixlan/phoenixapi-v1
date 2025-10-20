from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow

from phoenixRest.models.crew.position import Position

from phoenixRest.resource import resource

from phoenixRest.roles import ADMIN, MEMBER

from phoenixRest.models.crew.team import Team
from phoenixRest.models.crew.crew import Crew

from phoenixRest.views.position.instance import PositionInstanceResource

from phoenixRest.utils import validate

import logging
log = logging.getLogger(__name__)


@resource(name='position')
class PositionResource(object):
    __acl__ = [
        (Allow, MEMBER, 'getAll'),
        (Allow, ADMIN, 'create_position'),
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
    return request.db.query(Position).order_by(Position.name).all()

@view_config(context=PositionResource, name='', request_method='POST', renderer='json', permission='create_position')
@validate(json_body={'name': str, 'description': str})
def create_position(context, request):
    position = Position(request.json_body['name'], request.json_body['description'])

    position.chief = request.json_body['chief']
    position.is_vanity = request.json_body['is_vanity']

    # Add crew
    if request.json_body['crew_uuid'] is not None:
        crew = request.db.query(Crew).filter(Crew.uuid == request.json_body['crew_uuid']).first()
        if crew is None:
            request.response.status = 404
            return {
                "error": "Crew not found"
            }
        position.crew = crew

    # Add team
    if request.json_body['team_uuid'] is not None:
        team = request.db.query(Team).filter(Team.uuid == request.json_body['team_uuid']).first()

        if team is None:
            request.response.status = 404
            return {
                "error": "Team not found"
            }

        position.team = team
    request.db.add(position)
    request.db.flush()
    return position 