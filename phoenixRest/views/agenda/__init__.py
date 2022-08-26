from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPNotFound
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow


from phoenixRest.models import db
from phoenixRest.models.core.agenda_entry import AgendaEntry
from phoenixRest.models.core.event import Event, get_current_event

from phoenixRest.utils import validate
from phoenixRest.resource import resource

from phoenixRest.roles import ADMIN, EVENT_ADMIN, COMPO_ADMIN

from phoenixRest.views.agenda.instance import AgendaInstanceResource

from datetime import datetime

import logging
log = logging.getLogger(__name__)


@view_defaults(context='.AgendaViews')
@resource(name='agenda')
class AgendaViews(object):
    __acl__ = [
        (Allow, Everyone, 'get'),
        (Allow, ADMIN, 'create'),
        (Allow, EVENT_ADMIN, 'create'),
        (Allow, COMPO_ADMIN, 'create')
    ]
    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        node = AgendaInstanceResource(self.request, key)
        node.__parent__ = self
        node.__name__ = key
        return node

@view_config(context=AgendaViews, request_method='GET', renderer='json', permission='get')
def get_agenda_entries(request):
    # Find all events and sort them by start time
    entries = db.query(AgendaEntry).filter(AgendaEntry.event == get_current_event()).order_by(AgendaEntry.time.asc()).all()
    return entries 

@view_config(context=AgendaViews, request_method='PUT', renderer='json', permission='create')
@validate(json_body={'time': int, 'title': str, 'description': str, 'event_uuid': str})
def create_agenda_entry(context, request):
    event = db.query(Event).filter(Event.uuid == request.json_body['event_uuid']).first()

    if not event:
        request.response.status = 404
        return {
            "error": "Event not found"
        }

    entry = AgendaEntry(title=request.json_body['title'],
                        description=request.json_body['description'],
                        time=datetime.fromtimestamp(request.json_body['time']), 
                        event=event)
    db.add(entry)
    db.flush()
    return event

