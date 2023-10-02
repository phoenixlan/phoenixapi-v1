from pyramid.view import view_config, view_defaults
from pyramid.authorization import Authenticated, Everyone, Deny, Allow

from phoenixRest.models.core.agenda_entry import AgendaEntry
from phoenixRest.models.core.event import Event, get_current_event

from phoenixRest.utils import validate
from phoenixRest.resource import resource

from phoenixRest.roles import ADMIN, EVENT_ADMIN, COMPO_ADMIN, INFO_ADMIN

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
        (Allow, INFO_ADMIN, 'create'),
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
    # Find all events and sort them by start start_time
    entries = request.db.query(AgendaEntry).filter(AgendaEntry.event == get_current_event(request)).order_by(AgendaEntry.start_time.asc()).all()
    return entries 



@view_config(context=AgendaViews, request_method='PUT', renderer='json', permission='create')
@validate(json_body={'event_uuid': str, 'title': str, 'description': str, 'location': str, 'start_time': int, 'pinned': bool})
def create_agenda_entry(context, request):
    # Attempt to find current Event uuid
    event = request.db.query(Event).filter(Event.uuid == request.json_body['event_uuid']).first()

    if not event:
        request.response.status = 404
        return {
            "error": "Event not found"
        }

    entry = AgendaEntry(
        event=event,
        title=request.json_body['title'],
        description=request.json_body['description'],
        location=request.json_body['location'],
        start_time=datetime.fromtimestamp(int(request.json_body['start_time'])), 
        pinned=request.json_body['pinned'],
        created_by_user=request.user
    )
    request.db.add(entry)
    request.db.flush()
    return entry