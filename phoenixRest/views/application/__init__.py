from pyramid.view import view_config
from pyramid.authorization import Authenticated, Allow

from sqlalchemy import and_
from sqlalchemy.orm import joinedload

from phoenixRest.models.crew.application import Application
from phoenixRest.models.crew.application_crew_mapping import ApplicationCrewMapping

from phoenixRest.resource import resource

from phoenixRest.roles import ADMIN

from phoenixRest.views.application.instance import ApplicationInstanceResource

import logging
log = logging.getLogger(__name__)

@resource(name='application')
class ApplicationViews(object):
    __acl__ = [
        (Allow, ADMIN(), 'list'),

        (Allow, Authenticated, 'self'),
        # Authenticated pages
        #(Allow, Authenticated, Authenticated),
        #(Deny, Everyone, Authenticated),
    ]
    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        """Traverse to a specific application item"""
        if key in ['my']:
            raise KeyError('')
        node = ApplicationInstanceResource(self.request, key)
        node.__parent__ = self
        node.__name__ = key
        return node

@view_config(context=ApplicationViews, name='', request_method='GET', renderer='json', permission='list')
def get_all_applications(request):
    # TODO get for multiple applications
    # Find all applications and sort them by time created
    applications = request.db \
        .query(Application) \
        .options(joinedload(Application.user)) \
        .options(joinedload(Application.event)) \
        .options(joinedload(Application.crews).joinedload(ApplicationCrewMapping.crew)) \
        .order_by(Application.created.asc()).all()

    return applications

@view_config(context=ApplicationViews, name='my', request_method='GET', renderer='json', permission='self')
def get_applications_mine(request):
    # Find all applications and sort them by time created
    applications = request.db.query(Application) \
        .filter(and_(
            Application.user == request.user,
            Application.hidden == False
        )) \
        .order_by(Application.created.asc()).all()
    return applications
