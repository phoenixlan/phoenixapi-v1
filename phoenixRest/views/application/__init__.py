from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPNotFound,
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow


from phoenixRest.models.core.event import Event

from phoenixRest.models.crew.crew import Crew
from phoenixRest.models.crew.application import Application

from phoenixRest.utils import validate
from phoenixRest.resource import resource

from phoenixRest.roles import ADMIN, CHIEF

from phoenixRest.views.application.instance import ApplicationInstanceResource

from datetime import datetime

import logging
log = logging.getLogger(__name__)

@resource(name='application')
class ApplicationViews(object):
    __acl__ = [
        (Allow, CHIEF, 'list'),
        (Allow, ADMIN, 'list'),

        (Allow, Everyone, 'self'),
        (Allow, Everyone, 'create'),

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
def get_applications(request):
    # TODO get for multiple applications
    # Find all applications and sort them by time created
    applications = request.db.query(Application).order_by(Application.created.asc()).all()
    return applications

@view_config(context=ApplicationViews, name='', request_method='OPTIONS', renderer='string')
def get_applications_cors(request):
    return ""

@view_config(context=ApplicationViews, name='my', request_method='GET', renderer='json', permission='self')
def get_applications_mine(request):
    # Find all applications and sort them by time created
    applications = request.db.query(Application).filter(Application.user == request.user).order_by(Application.created.asc()).all()
    return applications

@view_config(context=ApplicationViews, name='my', request_method='OPTIONS', renderer='string')
def get_applications_mine_cors(request):
    return ""

@view_config(context=ApplicationViews, name='', request_method='PUT', renderer='json', permission='create')
@validate(json_body={'crew_uuid': str, 'contents': str})
def create_application(context, request):
    crew = request.db.query(Crew).filter(Crew.uuid == request.json_body['crew_uuid']).first()
    if crew is None:
        request.response.status = 404
        return {
            "error": "Crew not found"
        }

    if not crew.is_applyable:
        request.response.status = 400
        return {
            "error": "You applied to a crew that is not applyable"
        }
    
    if request.user.avatar is None:
        request.response.status = 400
        return {
            "error": "You must upload an avatar before you can apply for crew"
        }

    # Fetch current event
    event = request.db.query(Event).filter(Event.start_time > datetime.now()).order_by(Event.start_time.asc()).first()


    application = Application(user=request.user, 
                        crew=crew, 
                        event=event,
                        contents=request.json_body['contents'])
    request.db.add(application)
    request.db.flush()

    request.mail_service.send_mail(request.user.email, "Mottatt søknad", "application_received.jinja2", {
        "mail": request.registry.settings["api.contact"],
        "name": request.registry.settings["api.name"],
        "crew": crew
    })

    return application
