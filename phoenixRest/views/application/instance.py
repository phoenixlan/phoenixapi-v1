from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPNotFound,
    HTTPBadRequest
)
from pyramid.security import Authenticated, Everyone, Deny, Allow

from phoenixRest.models import db
from phoenixRest.models.crew.application import Application, ApplicationState

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
        self.applicationInstance = db.query(Application).filter(Application.uuid == uuid).first()

        if self.applicationInstance is None:
            raise HTTPNotFound("Application not found")

@view_config(context=ApplicationInstanceResource, name='', request_method='GET', renderer='json', permission='application_get')
def get_application(context, request):
    return context.applicationInstance

@view_config(context=ApplicationInstanceResource, name='', request_method='PATCH', renderer='json', permission='application_edit')
@validate(json_body={'state': str, 'answer': str})
def edit_application(context, request):
    if request.json_body['state'] not in ['accepted', 'rejected']:
        raise HTTPBadRequest('new state is not accepted or rejected')
    
    context.applicationInstance.state = ApplicationState.accepted if request.json_body["state"] == "accepted" else ApplicationState.rejected
    context.applicationInstance.answer = request.json_body["answer"]

    db.save(context.applicationInstance)

    return context.applicationInstance 
