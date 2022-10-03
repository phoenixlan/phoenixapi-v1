from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPNotFound,
    HTTPBadRequest
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow

from phoenixRest.models.crew.application import Application, ApplicationState
from phoenixRest.models.crew.position import create_or_fetch_crew_position

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
    
    context.applicationInstance.state = ApplicationState.accepted if request.json_body["state"] == "accepted" else ApplicationState.rejected
    context.applicationInstance.answer = request.json_body["answer"]
    context.applicationInstance.last_processed_by = request.user

    request.db.add(context.applicationInstance)
    
    if context.applicationInstance.state == ApplicationState.accepted:
        position = create_or_fetch_crew_position(request, crew=context.applicationInstance.crew, team=None)
        if position is None:
            request.response.status = 500
            return {
                'error': "Unable to get position"
            }
        position.users.append(context.applicationInstance.user)

    # Send mail
    name = request.registry.settings["api.name"]
    request.mail_service.send_mail(context.applicationInstance.user.email, "Vedrørende din crew-søknad til %s" % name, "application_response.jinja2", {
        "mail": request.registry.settings["api.contact"],
        "accepted": context.applicationInstance.state == ApplicationState.accepted,
        "name": name,
        "application": context.applicationInstance,
        "domain": request.registry.settings["api.mainpage"]
    })

    return context.applicationInstance 
