from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow


from phoenixRest.models.tickets.seatmap import Seatmap
from phoenixRest.models.tickets.row import Row

from phoenixRest.resource import resource

from phoenixRest.roles import ADMIN, TICKET_ADMIN

from phoenixRest.views.row.instance import RowInstanceResource

import logging
log = logging.getLogger(__name__)

@resource(name='row')
class RowResource(object):
    __acl__ = [
        (Allow, ADMIN, 'getAll'),
        (Allow, TICKET_ADMIN, 'getAll'),

        # Authenticated pages
        #(Allow, Authenticated, Authenticated),
        #(Deny, Everyone, Authenticated),
    ]
    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        """Traverse to a specific seatmap item"""
        node = RowInstanceResource(self.request, key)
        node.__parent__ = self
        node.__name__ = key
        return node

@view_config(name='', context=RowResource, request_method='GET', renderer='json', permission='getAll')
def get_all_rows(context, request):
    return request.db.query(Row).order_by(Row.name).all()





