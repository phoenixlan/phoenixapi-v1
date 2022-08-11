from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPNotFound
)
from pyramid.security import Authenticated, Everyone, Deny, Allow

from phoenixRest.models import db
from phoenixRest.models.crew.team import Team

from phoenixRest.utils import validate
from phoenixRest.resource import resource

from datetime import datetime

import logging
log = logging.getLogger(__name__)


class TeamInstanceViews(object):
    def __acl__(self):
        return [
        (Allow, Authenticated, 'team_view'),

        # Authenticated pages
        #(Allow, Authenticated, Authenticated),
        #(Deny, Everyone, Authenticated),
    ]

    def __init__(self, request, uuid):
        self.request = request
        self.teamInstance = db.query(Team).filter(Team.uuid == uuid).first()

        if self.teamInstance is None:
            raise HTTPNotFound("Team not found")

@view_config(context=TeamInstanceViews, name='', request_method='GET', renderer='json', permission='team_view')
def get_team(context, request):
    return self.teamInstance
