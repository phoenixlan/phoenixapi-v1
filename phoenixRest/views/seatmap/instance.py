from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPNotFound,
    HTTPBadRequest
)
from pyramid.security import Authenticated, Everyone, Deny, Allow

from phoenixRest.models import db
from phoenixRest.models.tickets.seatmap import Seatmap
from phoenixRest.models.tickets.entrance import Entrance
from phoenixRest.models.tickets.ticket_type import TicketType
from phoenixRest.models.tickets.row import Row
from phoenixRest.models.tickets.seatmap_background import SeatmapBackground

from phoenixRest.roles import ADMIN, TICKET_ADMIN

from phoenixRest.utils import validate, validateUuidAndQuery
from phoenixRest.resource import resource

from datetime import datetime

import os
import shutil

import logging
log = logging.getLogger(__name__)


class SeatmapInstanceViews(object):
    def __acl__(self):
        return [
        (Allow, Authenticated, 'seatmap_view'),
        (Allow, ADMIN, 'create_row'),
        (Allow, TICKET_ADMIN, 'create_row'),

        (Allow, ADMIN, 'upload_background'),
        (Allow, TICKET_ADMIN, 'upload_background'),
        # Authenticated pages
        #(Allow, Authenticated, Authenticated),
        #(Deny, Everyone, Authenticated),
    ]

    def __init__(self, request, uuid):
        self.request = request

        self.seatmapInstance = validateUuidAndQuery(Seatmap, Seatmap.uuid, uuid)

        if self.seatmapInstance is None:
            raise HTTPNotFound("Seatmap not found")

@view_config(context=SeatmapInstanceViews, name='', request_method='GET', renderer='json', permission='seatmap_view')
def get_seatmap(context, request):
    return context.seatmapInstance

@view_config(context=SeatmapInstanceViews, name='background', request_method='PUT', renderer='json', permission='upload_background')
def upload_background(context, request):
    if "file" not in request.POST:
        raise HTTPBadRequest("No file specified")
    
    background_dir = request.registry.settings["ticket.seatmap_background_location"]
    if not os.path.exists(background_dir):
        os.makedirs(background_dir)

    filename = request.POST['file'].filename
    log.debug("Got file upload with original name %s" % filename)

    extension = filename.split(".")[-1]

    background = SeatmapBackground(request.user, extension)
    db.add(background)
    db.flush()

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


@view_config(context=SeatmapInstanceViews, name='row', request_method='PUT', renderer='json', permission='create_row')
@validate(json_body={'row_number': int, 'x': int, 'y': int, 'horizontal': bool})
def create_row(context, request):
    # Creating a new row
    ticket_type = None
    if "ticket_type" in request.json_body:
        ticket_type = db.query(TicketType).filter(TicketType.uuid == request.json_body['ticket_type']).first()
        if ticket_type is None:
            raise HTTPBadRequest("Ticket type not found")

    entrance = None
    if "entrance" in request.json_body:
        entrance = db.query(Entrance).filter(Entrance.uuid == request.json_body['entrance']).first()
        if entrance is None:
            raise HTTPBadRequest("Entrance not found")

    row = Row( \
        request.json_body['row_number'], \
        request.json_body['x'], \
        request.json_body['y'], \
        request.json_body['horizontal'], \
        context.seatmapInstance, \
        entrance, \
        ticket_type \
    )

    db.add(row)
    db.flush()
    return row


