from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPNotFound
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow

from phoenixRest.models import db
from phoenixRest.models.crew.crew import Crew
from phoenixRest.models.crew.team import Team

from phoenixRest.mappers.crew import map_crew

from phoenixRest.roles import ADMIN, MEMBER

from phoenixRest.utils import validate
from phoenixRest.resource import resource

from datetime import datetime

import logging
log = logging.getLogger(__name__)


class CrewInstanceViews(object):
    def __acl__(self):
        return [
        (Allow, Authenticated, 'team_view'),
        (Allow, MEMBER, 'crew_view'),
        (Allow, ADMIN, 'team_edit'),
        (Allow, 'chief:%s' % self.crewInstance.uuid, 'team_edit'),

        # Authenticated pages
        #(Allow, Authenticated, Authenticated),
        #(Deny, Everyone, Authenticated),
    ]

    def __init__(self, request, uuid):
        self.request = request
        self.crewInstance = db.query(Crew).filter(Crew.uuid == uuid).first()

        if self.crewInstance is None:
            raise HTTPNotFound("Crew not found")

@view_config(context=CrewInstanceViews, name='team', request_method='GET', renderer='json', permission='team_view')
def list_teams(context, request):
    log.info("Listing teams for crew %s" % context.crewInstance.name)
    teams = db.query(Team).filter(Team.crew == context.crewInstance).all()
    return teams

@view_config(context=CrewInstanceViews, name='team', request_method='PUT', renderer='json', permission='team_edit')
@validate(json_body={'name': str, 'description': str})
def create_team(context, request):
    team = Team(context.crewInstance, request.json_body['name'], request.json_body['description'])
    db.add(team)
    return team

@view_config(context=CrewInstanceViews, name='', request_method='GET', renderer='json', permission='crew_view')
def get_crew(context, request):
    return map_crew(context.crewInstance, request)
    

