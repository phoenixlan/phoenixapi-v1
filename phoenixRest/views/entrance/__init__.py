from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow

from phoenixRest.models.tickets.entrance import Entrance

from phoenixRest.utils import validate
from phoenixRest.resource import resource

from phoenixRest.roles import ADMIN, TICKET_ADMIN

from phoenixRest.views.seatmap.instance import SeatmapInstanceViews

import logging
log = logging.getLogger(__name__)

@resource(name='entrance')
class EntranceResource(object):
    __acl__ = [
        (Allow, Everyone, 'getAll'),
        (Allow, ADMIN, 'create'),
        (Allow, TICKET_ADMIN, 'create'),

        # Authenticated pages
        #(Allow, Authenticated, Authenticated),
        #(Deny, Everyone, Authenticated),
    ]
    def __init__(self, request):
        self.request = request

@view_config(name='', context=EntranceResource, request_method='GET', renderer='json', permission='getAll')
def get_all_entrances(context, request):
    return request.db.query(Entrance).order_by(Entrance.name).all()

@view_config(name='', context=EntranceResource, request_method='POST', renderer='json', permission='create')
@validate(json_body={'name': str})
def create_entrance(context, request):
    entrance = Entrance(request.json_body['name'])
    request.db.add(entrance)
    request.db.flush()
    return entrance



