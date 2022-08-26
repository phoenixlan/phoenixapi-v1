from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPNotFound,
    HTTPBadRequest
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow

from phoenixRest.models import db
from phoenixRest.models.tickets.seat import Seat
from phoenixRest.models.tickets.row import Row

from phoenixRest.roles import ADMIN, TICKET_ADMIN

from phoenixRest.utils import validate, validateUuidAndQuery
from phoenixRest.resource import resource

from datetime import datetime

import logging
log = logging.getLogger(__name__)


class RowInstanceResource(object):
    def __acl__(self):
        return [
        (Allow, ADMIN, 'create_seat'),
        (Allow, TICKET_ADMIN, 'create_seat'),
        (Allow, ADMIN, 'update_row'),
        (Allow, TICKET_ADMIN, 'update_row'),
        # Authenticated pages
        #(Allow, Authenticated, Authenticated),
        #(Deny, Everyone, Authenticated),
    ]

    def __init__(self, request, uuid):
        self.request = request

        self.rowInstance = validateUuidAndQuery(Row, Row.uuid, uuid)

        if self.rowInstance is None:
            raise HTTPNotFound("Row not found")

@view_config(context=RowInstanceResource, name='', request_method='PATCH', renderer='json', permission='update_row')
def update_row(context, request):
    if 'x' in request.json_body:
        context.rowInstance.x = request.json_body['x']
    
    if 'y' in request.json_body:
        context.rowInstance.y = request.json_body['y']

    if 'row_number' in request.json_body:
        context.rowInstance.row_number = request.json_body['row_number']
    
    if 'is_horizontal' in request.json_body:
        context.rowInstance.is_horizontal = request.json_body['is_horizontal']
    
    db.add(context.rowInstance)
    db.flush()
    return context.rowInstance
    
@view_config(context=RowInstanceResource, name='seat', request_method='PUT', renderer='json', permission='create_seat')
def create_seat(context, request):
    existing = db.query(Seat).where(Seat.row_uuid == context.rowInstance.uuid).all()
    seat = Seat(len(existing)+1, context.rowInstance)

    db.add(seat)
    db.flush()
    return seat


