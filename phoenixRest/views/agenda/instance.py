from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPNotFound,
    HTTPBadRequest
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow

from phoenixRest.utils import validate

from phoenixRest.models.core.user import User
from phoenixRest.models.core.agenda_entry import AgendaEntry

from phoenixRest.roles import ADMIN, EVENT_ADMIN, CHIEF, INFO_ADMIN, COMPO_ADMIN

from datetime import datetime

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
        self.agendaInstance = request.db.query(AgendaEntry).filter(AgendaEntry.uuid == uuid).first()

        if self.agendaInstance is None:
            raise HTTPNotFound("Agenda not found")

@view_config(context=AgendaInstanceResource, name='', request_method='GET', renderer='json', permission='agenda_get')
def get_instance(context, request):
    return context.agendaInstance

@view_config(context=AgendaInstanceResource, name='', request_method='DELETE', renderer='json', permission='agenda_delete')
def delete_agenda_entry(context, request):
    request.db.delete(context.agendaInstance)

# Modify agenda entry
@view_config(context=AgendaInstanceResource, request_method='PATCH', renderer='json', permission='create')
def modify_agenda_entry(context, request):

    if 'title' in request.json_body:
        if type(request.json_body['title']) == str:
            context.agendaInstance.title = request.json_body['title']
        else:
            request.response.status = 400
            return {
                'error': 'Invalid type for title (not string)'
            }
        
    if 'description' in request.json_body:
        if type(request.json_body['description']) == str:
            context.agendaInstance.description = request.json_body['description']
        else:
            request.response.status = 400
            return {
                'error': 'Invalid type for description (not string)'
            }
        
    if 'location' in request.json_body:
        if type(request.json_body['location']) == str:
            context.agendaInstance.location = request.json_body['location']
        else:
            request.response.status = 400
            return {
                'error': 'Invalid type for location (not string)'
            }
        
    if 'time' in request.json_body:
        if type(request.json_body['time']) == int:
            context.agendaInstance.time = datetime.fromtimestamp(int(request.json_body['time']))
        else:
            request.response.status = 400
            return {
                'error': 'Invalid type of time (not integer)'
            }

    if 'deviating_time' in request.json_body:
        if type(request.json_body['deviating_time']) == int:
            context.agendaInstance.deviating_time = datetime.fromtimestamp(int(request.json_body['deviating_time']))  
        elif request.json_body['deviating_time'] == None:
            context.agendaInstance.deviating_time = None
        else:
            request.response.status = 400
            return {
                'error': 'Invalid type of deviating_time (not integer)'
            }

    if 'deviating_time_unknown' in request.json_body:
        if type(request.json_body['deviating_time_unknown']) == bool:
            context.agendaInstance.deviating_time_unknown = request.json_body['deviating_time_unknown']
        else:
            request.response.status = 400
            return {
                'error': 'Invalid type of deviating_time_unknown (not boolean)'
            }
        
    if 'deviating_location' in request.json_body:
        if type(request.json_body['deviating_location']) == str:
            context.agendaInstance.deviating_location = request.json_body['deviating_location']
        else:
            request.response.status = 400
            return {
                'error': 'Invalid type of deviating_location (not string)'
            }
        
    if 'deviating_information' in request.json_body:
        if type(request.json_body['deviating_information']) == str:
            context.agendaInstance.deviating_information = request.json_body['deviating_information']
        else:
            request.response.status = 400
            return {
                'error': 'Invalid type of deviating_information (not string)'
            }
        
    if 'pinned' in request.json_body:
        if type(request.json_body['pinned']) == bool:
            context.agendaInstance.pinned = request.json_body['pinned']
        else:
            request.response.status = 400
            return {
                'error': 'Invalid type of pinned (not boolean)'
            }
        
    if 'cancelled' in request.json_body:
        if type(request.json_body['cancelled']) == bool:
            context.agendaInstance.cancelled = request.json_body['cancelled']
        else:
            request.response.status = 400
            return {
                'error': 'Invalid type of cancelled (not boolean)'
            }
    
    context.agendaInstance.modified_by_user = request.user
    context.agendaInstance.modified = datetime.now()

    return context.agendaInstance
    


