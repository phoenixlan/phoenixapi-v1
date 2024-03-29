from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPNotFound,
    HTTPBadRequest
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow

from phoenixRest.models.core.event import Event, get_current_event
from phoenixRest.models.tickets.seatmap import Seatmap
from phoenixRest.models.tickets.entrance import Entrance
from phoenixRest.models.tickets.ticket_type import TicketType
from phoenixRest.models.tickets.row import Row
from phoenixRest.models.tickets.seat import Seat
from phoenixRest.models.tickets.ticket import Ticket
from phoenixRest.models.tickets.seatmap_background import SeatmapBackground

from phoenixRest.mappers.seatmap import map_seatmap_for_availability

from phoenixRest.roles import ADMIN, TICKET_ADMIN

from phoenixRest.utils import validate, validateUuidAndQuery
from phoenixRest.resource import resource

from sqlalchemy import and_

from datetime import datetime

import os
import shutil
import json

import logging
log = logging.getLogger(__name__)


class SeatmapInstanceViews(object):
    def __acl__(self):
        return [
        (Allow, Authenticated, 'seatmap_get_availability'),
        (Allow, ADMIN, 'create_row'),
        (Allow, TICKET_ADMIN, 'create_row'),

        (Allow, ADMIN, 'upload_background'),
        (Allow, TICKET_ADMIN, 'upload_background'),

        (Allow, ADMIN, 'seatmap_view'),
        (Allow, TICKET_ADMIN, 'seatmap_view'),
        # Authenticated pages
        #(Allow, Authenticated, Authenticated),
        #(Deny, Everyone, Authenticated),
    ]

    def __init__(self, request, uuid):
        self.request = request

        self.seatmapInstance = validateUuidAndQuery(request, Seatmap, Seatmap.uuid, uuid)

        if self.seatmapInstance is None:
            raise HTTPNotFound("Seatmap not found")

@view_config(context=SeatmapInstanceViews, name='', request_method='GET', renderer='json', permission='seatmap_view')
def get_seatmap(context, request):
    return context.seatmapInstance

@view_config(context=SeatmapInstanceViews, name='availability', request_method='GET', renderer='json', permission='seatmap_get_availability')
def get_seatmap_availability(context, request):
    event = None
    if 'event_uuid' in request.GET:
        event = request.db.query(Event).filter(Event.uuid == request.GET['event_uuid']).first()
        if event is None:
            request.response.status = 404
            return {
                'error': "Event not found"
            }
    else:
        event = get_current_event(request)
    
    seatmap = request.db.query(Seatmap) \
        .join(Row, Row.seatmap_uuid == Seatmap.uuid) \
        .join(Seat, Seat.row_uuid == Row.uuid) \
        .join(Ticket, Ticket.seat_uuid == Seat.uuid, isouter=True) \
        .filter(Seatmap.uuid == context.seatmapInstance.uuid) \
        .first()

    return map_seatmap_for_availability(seatmap, request)


@view_config(context=SeatmapInstanceViews, name='background', request_method='PUT', renderer='json', permission='upload_background')
def upload_background(context, request):
    if "file" not in request.POST:
        request.response.status = 400
        return {
            "error": "No file specified"
        }
    
    background_dir = request.registry.settings["ticket.seatmap_background_location"]
    if not os.path.exists(background_dir):
        os.makedirs(background_dir)

    filename = request.POST['file'].filename
    log.debug("Got file upload with original name %s" % filename)

    extension = filename.split(".")[-1]

    background = SeatmapBackground(request.user, extension)
    request.db.add(background)
    request.db.flush()

    # Copy the file
    file_path = background.get_fs_location(request)

    temp_file_path = file_path + '~'

    # Finally write the data to a temporary file
    input_file = request.POST['file'].file
    input_file.seek(0)
    with open(temp_file_path, 'wb') as output_file:
        shutil.copyfileobj(input_file, output_file)

    # Now that we know the file has been fully saved to disk move it into place.
    os.rename(temp_file_path, file_path)

    context.seatmapInstance.background = background
    return {
        "status": "ok"
    }


@view_config(context=SeatmapInstanceViews, name='row', request_method='PUT', renderer='json', permission='create_row')
@validate(json_body={'row_number': int, 'x': int, 'y': int, 'horizontal': bool})
def create_row(context, request):
    # Creating a new row
    ticket_type = None
    if "ticket_type" in request.json_body:
        ticket_type = request.db.query(TicketType).filter(TicketType.uuid == request.json_body['ticket_type']).first()
        if ticket_type is None:
            request.response.status = 400
            return {
                "error": "Ticket type not found"
            }

    entrance = None
    if "entrance" in request.json_body:
        entrance = request.db.query(Entrance).filter(Entrance.uuid == request.json_body['entrance']).first()
        if entrance is None:
            request.response.status = 400
            return {
                "error": "Entrance not found"
            }

    row = Row( \
        request.json_body['row_number'], \
        request.json_body['x'], \
        request.json_body['y'], \
        request.json_body['horizontal'], \
        context.seatmapInstance, \
        entrance, \
        ticket_type \
    )

    request.db.add(row)
    request.db.flush()
    return row


