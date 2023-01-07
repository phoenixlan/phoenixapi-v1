from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPNotFound,
    HTTPBadRequest
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow

from phoenixRest.models.crew.crew import Crew
from phoenixRest.models.crew.application import Application, ApplicationState
from phoenixRest.models.crew.position import create_or_fetch_crew_position
from phoenixRest.models.crew.position_mapping import PositionMapping
from phoenixRest.models.core.event import get_current_event

from phoenixRest.roles import ADMIN, CHIEF

from phoenixRest.utils import validate
from phoenixRest.resource import resource

from datetime import datetime
import os

import logging
log = logging.getLogger(__name__)

from PIL import Image

class ApplicationInstanceResource(object):
    def __acl__(self):
        acl = [
            (Allow, "%s" % self.applicationInstance.user.uuid, 'application_get'),
            (Allow, ADMIN, 'application_get'),
            (Allow, CHIEF, 'application_get'),

            (Allow, ADMIN, 'application_edit'),
            (Allow, CHIEF, 'application_edit'),
        ]
        return acl

    def __init__(self, request, uuid):
        self.request = request
        self.applicationInstance = request.db.query(Application).filter(Application.uuid == uuid).first()

        if self.applicationInstance is None:
            raise HTTPNotFound("Application not found")

@view_config(context=ApplicationInstanceResource, name='', request_method='GET', renderer='json', permission='application_get')
def get_application(context, request):
    return context.applicationInstance

@view_config(context=ApplicationInstanceResource, name='', request_method='PATCH', renderer='json', permission='application_edit')
@validate(json_body={'state': str, 'answer': str})
def edit_application(context, request):
    if request.json_body['state'] not in ['accepted', 'rejected']:
        request.response.status = 400
        return {
            "error": "Invalid state"
        }
    # We can accept applications multiple times(if we accept multiple crew applications). But not if the application is rejected
    if request.json_body['state'] == "accepted" and context.applicationInstance.state == ApplicationState.rejected:
        request.response.status = 400
        return {
            "error": "Cannot approve an application that has been denied"
        }

    context.applicationInstance.state = ApplicationState.accepted if request.json_body["state"] == "accepted" else ApplicationState.rejected
    context.applicationInstance.answer = request.json_body["answer"]
    context.applicationInstance.last_processed_by = request.user

    request.db.add(context.applicationInstance)
    
    accepted_crew = None
    if context.applicationInstance.state == ApplicationState.accepted:
        # Fetch the accepted crew
        accepted_crew = request.db.query(Crew).filter(Crew.uuid == request.json_body['crew_uuid']).first()
        if accepted_crew is None:
            request.response.status = 404
            return {
                "error": "Accepted crew doesn't exist"
            }
        # Mark the application-crew mapping as accepted
        for mapping in context.applicationInstance.crews:
            if mapping.crew == accepted_crew:
                if mapping.accepted:
                    request.response.stauts = 400
                    return {
                        "error": "Application has already been accepted for this crew"
                    }
                mapping.accepted = True
        
        position = create_or_fetch_crew_position(request, crew=accepted_crew, team=None)
        if position is None:
            request.response.status = 500
            return {
                'error': "Unable to get position"
            }

        mapping = PositionMapping(context.applicationInstance.user, position, get_current_event(request))
        position.position_mappings.append(mapping)

    # Send mail
    name = request.registry.settings["api.name"]
    log.info("Registered change in application - sending e-mail")
    request.mail_service.send_mail(context.applicationInstance.user.email, "Vedrørende din crew-søknad til %s" % name, "application_response.jinja2", {
        "mail": request.registry.settings["api.contact"],
        "accepted": context.applicationInstance.state == ApplicationState.accepted,
        "accepted_crew": accepted_crew,
        "name": name,
        "application": context.applicationInstance,
        "domain": request.registry.settings["api.mainpage"]
    })

    return context.applicationInstance 
