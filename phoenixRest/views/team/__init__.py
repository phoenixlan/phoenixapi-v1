from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow

from phoenixRest.resource import resource

from phoenixRest.roles import ADMIN

from phoenixRest.views.team.instance import TeamInstanceViews

import logging
log = logging.getLogger(__name__)


@resource(name='team')
class TeamViews(object):
    __acl__ = [
        (Allow, Everyone, 'current::get'),
        (Allow, Everyone, 'get'),
        (Allow, ADMIN, 'create'),

        # Authenticated pages
        #(Allow, Authenticated, Authenticated),
        #(Deny, Everyone, Authenticated),
    ]
    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        """Traverse to a specific crew item"""
        node = TeamInstanceViews(self.request, key)
        node.__parent__ = self
        node.__name__ = key
        return node

# TODO: Thea! Fill inn stuff her!