from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPNotFound,
    HTTPBadRequest
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow

from phoenixRest.models.core.event_brand import EventBrand
from phoenixRest.models.core.event import Event, get_current_event
from phoenixRest.models.tickets.seatmap import Seatmap
from phoenixRest.models.tickets.ticket_type import TicketType

from phoenixRest.roles import ADMIN, BRAND_ADMIN, TICKET_ADMIN
from phoenixRest.utils import validate

from datetime import datetime

class EventBrandInstanceResource(object):
    def __acl__(self):
        acl = [
            (Allow, Everyone, 'get'),
            (Allow, Everyone, 'get_current_event'),
            (Allow, ADMIN(), 'create_event'),
            (Allow, BRAND_ADMIN(self.eventBrandInstance.uuid), 'create_event'),
            (Allow, ADMIN(), 'create_ticket_type'),
            (Allow, BRAND_ADMIN(self.eventBrandInstance.uuid), 'create_ticket_type'),
            (Allow, TICKET_ADMIN(self.eventBrandInstance.uuid), 'create_ticket_type'),
            (Allow, ADMIN(), 'get_all_seatmaps'),
            (Allow, TICKET_ADMIN(self.eventBrandInstance.uuid), 'get_all_seatmaps'),
        ]
        return acl

    def __init__(self, request, uuid):
        self.request = request
        self.eventBrandInstance = request.db.query(EventBrand).filter(EventBrand.uuid == uuid).first()

        if self.eventBrandInstance is None:
            raise HTTPNotFound("Event brand not found")


@view_config(context=EventBrandInstanceResource, name='', request_method='GET', renderer='json', permission='get')
def get_event_brand(context, request):
    return context.eventBrandInstance

@view_config(context=EventBrandInstanceResource, name='current_event', request_method='GET', renderer='json', permission='get_current_event')
def get_active_event(context, request):
    return get_current_event(request.db, context.eventBrandInstance)

@view_config(context=EventBrandInstanceResource, name='event', request_method='PUT', renderer='json', permission='create_event')
@validate(json_body={'name': str, 'start_time': int, 'end_time': int, 'max_participants': int})
def create_event(context, request):
    event = Event(
        name=request.json_body['name'],
        start_time=datetime.fromtimestamp(request.json_body['start_time']),
        end_time=datetime.fromtimestamp(request.json_body['end_time']),
        max_participants=request.json_body['max_participants'],
        event_brand=context.eventBrandInstance
    )
    request.db.add(event)
    request.db.flush()
    return event

@view_config(context=EventBrandInstanceResource, name='ticket_type', request_method='POST', renderer='json', permission='create_ticket_type')
@validate(json_body={'name': str, 'price': int, 'refundable': bool, 'seatable': bool, 'description': str})
def create_ticket_type(context, request):
    ticket_type = TicketType(
        request.json_body['name'],
        request.json_body['price'],
        request.json_body['description'],
        request.json_body['refundable'],
        request.json_body['seatable']
    )
    ticket_type.event_brand = context.eventBrandInstance
    request.db.add(ticket_type)
    request.db.flush()
    return ticket_type

@view_config(context=EventBrandInstanceResource, name='seatmap', request_method='GET', renderer='json', permission='get_all_seatmaps')
def get_all_seatmaps(context, request):
    return request.db.query(Seatmap) \
        .filter(Seatmap.event_brand_uuid == context.eventBrandInstance.uuid) \
        .order_by(Seatmap.name) \
        .all()
