from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPNotFound,
    HTTPBadRequest
)
from pyramid.security import Authenticated, Everyone, Deny, Allow

from phoenixRest.models import db
from phoenixRest.models.core.agenda_entry import AgendaEntry

from phoenixRest.mappers.crew import map_crew

from phoenixRest.roles import ADMIN, EVENT_ADMIN, CHIEF

from phoenixRest.utils import validate
from phoenixRest.resource import resource

from datetime import datetime
import os

import logging
log = logging.getLogger(__name__)

from PIL import Image

class AgendaInstanceResource(object):
    def __acl__(self):
        acl = [
            (Allow, Everyone, 'agenda_get'),
            (Allow, ADMIN, 'agenda_get'),
            (Allow, EVENT_ADMIN, 'agenda_get'),

            (Allow, EVENT_ADMIN, 'agenda_delete'),
            (Allow, ADMIN, 'agenda_delete'),
        ]
        return acl

    def __init__(self, request, uuid):
        self.request = request
        self.agendaInstance= db.query(AgendaEntry).filter(AgendaEntry.uuid == uuid).first()

        if self.agendaInstance is None:
            raise HTTPNotFound("Agenda not found")

@view_config(context=AgendaInstanceResource, name='', request_method='GET', renderer='json', permission='agenda_get')
def get_event(context, request):
    return context.agendaInstance

# Objects relating to the specific event
@view_config(context=AgendaInstanceResource, name='', request_method='DELETE', renderer='json', permission='agenda_delete')
def get_applications(context, request):
    db.delete(context.agendaInstance)


