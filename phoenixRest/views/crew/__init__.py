from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
)
from pyramid.security import Authenticated, Everyone, Deny, Allow


from phoenixRest.models import db
from phoenixRest.models.crew.crew import Crew
from phoenixRest.models.core.event import Event

from phoenixRest.utils import validate
from phoenixRest.resource import resource

from phoenixRest.roles import ADMIN

from phoenixRest.views.crew.instance import CrewInstanceViews

from datetime import datetime

import logging
log = logging.getLogger(__name__)

@view_defaults(context='.CrewViews')
@resource(name='crew')
class CrewViews(object):
    __acl__ = [
        (Allow, Everyone, 'get'),
        (Allow, Everyone, 'getAll'),
        (Allow, ADMIN, 'create'),

        # Authenticated pages
        #(Allow, Authenticated, Authenticated),
        #(Deny, Everyone, Authenticated),
    ]
    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        """Traverse to a specific crew item"""
        node = CrewInstanceViews(self.request, key)
        node.__parent__ = self
        node.__name__ = key
        return node

@view_config(context=CrewViews, name='', request_method='GET', renderer='json', permission='getAll')
def get_all_crew(request):
    # Returns all crews
    query = db.query(Crew)

    log.debug("Principals: %s" % request.effective_principals)
    if "role:admin" not in request.effective_principals:
        log.info("Reducing crew list as the requester is not admin")
        query = query.filter(Crew.active == True)
    
    return query.order_by(Crew.name).all()

@view_config(context=CrewViews, request_method='PUT', renderer='json', permission='create')
@validate(json_body={'name': str, 'description': str})
def create_crew(request):
    crew = Crew(name=request.json_body['name'], 
                  description=request.json_body['description'])
    db.add(crew)
    return crew

