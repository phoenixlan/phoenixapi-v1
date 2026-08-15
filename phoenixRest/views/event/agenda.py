from pyramid.authorization import Allow, Everyone
from pyramid.view import view_config

from phoenixRest.models.core.agenda_entry import AgendaEntry

from phoenixRest.roles import ADMIN, BRAND_ADMIN, COMPO_ADMIN, INFO_ADMIN
from phoenixRest.utils import validate

from phoenixRest.views.agenda.instance import AgendaInstanceResource

from datetime import datetime

class EventAgendaResource(object):
    def __acl__(self):
        return [
            (Allow, Everyone, 'list_agenda_entries'),
            (Allow, ADMIN(), 'create'),
            (Allow, BRAND_ADMIN(self.event.event_brand_uuid), 'create'),
            (Allow, INFO_ADMIN(self.event.event_brand_uuid), 'create'),
            (Allow, COMPO_ADMIN(self.event.event_brand_uuid), 'create')
        ]

    def __init__(self, request, event):
        self.request = request
        self.event = event

@view_config(context=EventAgendaResource, request_method='GET', renderer='json', permission='list_agenda_entries')
def get_agenda_entries(context, request):
    entries = request.db.query(AgendaEntry).filter(AgendaEntry.event == context.event).order_by(AgendaEntry.time.asc()).all()
    return entries

@view_config(context=EventAgendaResource, request_method='PUT', renderer='json', permission='create')
@validate(json_body={'title': str, 'description': str, 'location': str, 'time': int, 'duration': int, 'pinned': bool})
def create_agenda_entry(context, request):
    entry = AgendaEntry(
        event=context.event,
        title=request.json_body['title'],
        description=request.json_body['description'],
        location=request.json_body['location'],
        time=datetime.fromtimestamp(int(request.json_body['time'])),
        duration=request.json_body['duration'],
        pinned=request.json_body['pinned'],
        created_by_user=request.user
    )

    request.db.add(entry)
    request.db.flush()
    return entry
