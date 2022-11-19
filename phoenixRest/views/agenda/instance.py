from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPNotFound,
    HTTPBadRequest
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow

from phoenixRest.models.core.agenda_entry import AgendaEntry

from phoenixRest.roles import ADMIN, EVENT_ADMIN, CHIEF, INFO_ADMIN, COMPO_ADMIN

import logging
log = logging.getLogger(__name__)

class AgendaInstanceResource(object):
    def __acl__(self):
        acl = [
            (Allow, Everyone, 'agenda_get'),
            (Allow, ADMIN, 'agenda_get'),
            (Allow, EVENT_ADMIN, 'agenda_get'),
            (Allow, INFO_ADMIN, 'agenda_get'),
            (Allow, COMPO_ADMIN, 'agenda_get'),

            (Allow, EVENT_ADMIN, 'agenda_delete'),
            (Allow, ADMIN, 'agenda_delete'),
            (Allow, INFO_ADMIN, 'agenda_delete'),
            (Allow, COMPO_ADMIN, 'agenda_delete'),
        ]
        return acl

    def __init__(self, request, uuid):
        self.request = request
        self.agendaInstance= request.db.query(AgendaEntry).filter(AgendaEntry.uuid == uuid).first()

        if self.agendaInstance is None:
            raise HTTPNotFound("Agenda not found")

@view_config(context=AgendaInstanceResource, name='', request_method='GET', renderer='json', permission='agenda_get')
def get_event(context, request):
    return context.agendaInstance

# Objects relating to the specific event
@view_config(context=AgendaInstanceResource, name='', request_method='DELETE', renderer='json', permission='agenda_delete')
def get_applications(context, request):
    request.db.delete(context.agendaInstance)


