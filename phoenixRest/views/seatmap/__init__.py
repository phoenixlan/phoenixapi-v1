from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow


from phoenixRest.models.tickets.seatmap import Seatmap

from phoenixRest.utils import validate
from phoenixRest.resource import resource

from phoenixRest.roles import ADMIN, TICKET_ADMIN

from phoenixRest.views.seatmap.instance import SeatmapInstanceViews

import logging
log = logging.getLogger(__name__)

@resource(name='seatmap')
class SeatmapViews(object):
    __acl__ = [
        (Allow, Everyone, 'get'),
        (Allow, ADMIN, 'getAll'),
        (Allow, ADMIN, 'create'),
        (Allow, TICKET_ADMIN, 'getAll'),
        (Allow, TICKET_ADMIN, 'create'),

        # Authenticated pages
        #(Allow, Authenticated, Authenticated),
        #(Deny, Everyone, Authenticated),
    ]
    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        """Traverse to a specific seatmap item"""
        node = SeatmapInstanceViews(self.request, key)
        node.__parent__ = self
        node.__name__ = key
        return node

@view_config(name='', context=SeatmapViews, request_method='GET', renderer='json', permission='getAll')
def get_all_seatmaps(context, request):
    return request.db.query(Seatmap).order_by(Seatmap.name).all()

@view_config(name='', context=SeatmapViews, request_method='PUT', renderer='json', permission='create')
@validate(json_body={'name': str, 'description': str})
def create_seatmap(context, request):
    seatmap = Seatmap(request.json_body['name'], request.json_body['description'])
    request.db.add(seatmap)
    request.db.flush()
    return seatmap


