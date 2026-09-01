from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow

from phoenixRest.models.crew.position import Position

from phoenixRest.resource import resource

from phoenixRest.roles import ADMIN

from phoenixRest.models.crew.team import Team
from phoenixRest.models.crew.crew import Crew
from phoenixRest.models.core.event_brand import EventBrand

from phoenixRest.views.position.instance import PositionInstanceResource

from phoenixRest.utils import validate

import logging
log = logging.getLogger(__name__)


@resource(name='position')
class PositionResource(object):
    __acl__ = [
        (Allow, ADMIN(), 'getAll'),
        (Allow, ADMIN(), 'create_position'),
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

    crew = None
    if request.json_body['crew_uuid'] is not None:
        crew = request.db.query(Crew).filter(Crew.uuid == request.json_body['crew_uuid']).first()
        if crew is None:
            request.response.status = 400
            return {
                "error": "Crew not found"
            }

    team = None
    if request.json_body['team_uuid'] is not None:
        team = request.db.query(Team).filter(Team.uuid == request.json_body['team_uuid']).first()
        if team is None:
            request.response.status = 400
            return {
                "error": "Team not found"
            }

        if crew is not None and team.crew_uuid != crew.uuid:
            request.response.status = 400
            return {
                "error": "Team belongs to a different crew"
            }
        crew = team.crew

    event_brand = crew.event_brand if crew is not None else None
    if 'event_brand_uuid' in request.json_body:
        requested_brand = request.db.query(EventBrand).filter(
            EventBrand.uuid == request.json_body['event_brand_uuid']
        ).first()
        if requested_brand is None:
            request.response.status = 400
            return {
                "error": "Event brand not found"
            }
        if event_brand is not None and requested_brand.uuid != event_brand.uuid:
            request.response.status = 400
            return {
                "error": "Crew or team belongs to a different event brand"
            }
        event_brand = requested_brand

    if event_brand is None:
        if 'event_brand_uuid' not in request.json_body:
            request.response.status = 400
            return {
                "error": "Must set event brand if crew or team is not provided"
            }

    position.crew = crew
    position.team = team
    position.event_brand = event_brand
    request.db.add(position)
    request.db.flush()
    return position 
