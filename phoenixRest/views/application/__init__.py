from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPNotFound,
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow


from phoenixRest.models.core.event import Event, get_current_event

from phoenixRest.models.crew.crew import Crew
from phoenixRest.models.crew.application import Application
from phoenixRest.models.crew.application_crew_mapping import ApplicationCrewMapping

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
@validate(json_body={'crews': list, 'contents': str})
def create_application(context, request):
    if request.user.avatar is None:
        request.response.status = 400
        return {
            "error": "You must upload an avatar before you can apply for crew"
        }

    if len(request.json_body['crews']) > 3:
        request.response.status = 400
        return {
            "error": "Too many crews"
        }
    elif len(request.json_body['crews']) == 0:
        request.response.status = 400
        return {
            "error": "You need to apply to at least one crew"
        }

    if len(set(request.json_body['crews'])) != len(request.json_body['crews']):
        request.response.status = 400
        return {
            "error": "Duplicates are not allowed"
        }
    
    crew_list = list(map(lambda crew: request.db.query(Crew).filter(Crew.uuid == crew).first(), request.json_body['crews']))

    if None in crew_list:
        request.response.status = 404
        return {
            "error": "Crew not found"
        }
    
    for crew in crew_list:
        if not crew.is_applyable:
            request.response.status = 400
            return {
                "error": "You cannot apply to %s" % crew.name
            }
    
    # Fetch current event
    event = get_current_event(request)

    application = Application(user=request.user, 
                        event=event,
                        crews=list(map(lambda crew: ApplicationCrewMapping(crew), crew_list)),
                        contents=request.json_body['contents'])
    request.db.add(application)
    request.db.flush()

    request.mail_service.send_mail(request.user.email, "Mottatt søknad", "application_received.jinja2", {
        "mail": request.registry.settings["api.contact"],
        "name": request.registry.settings["api.name"],
        "crew_list": crew_list
    })

    return application
