from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPBadRequest,
    HTTPNotFound,
    HTTPInternalServerError
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow


from phoenixRest.models.tickets.payment import Payment

from phoenixRest.resource import resource

from phoenixRest.roles import ADMIN

from phoenixRest.views.payment.instance import PaymentInstanceResource

import logging
log = logging.getLogger(__name__)

@resource(name='payment')
class PaymentResource(object):
    __acl__ = [
        (Allow, ADMIN(), 'fetch_all'),

        # Authenticated pages
        #(Allow, Authenticated, Authenticated),
        #(Deny, Everyone, Authenticated),
    ]

    def __getitem__(self, key):
        """Traverse to a specific payment"""
        node = PaymentInstanceResource(self.request, key)
        node.__parent__ = self
        node.__name__ = key
        return node

    def __init__(self, request):
        self.request = request


@view_config(context=PaymentResource, name='', request_method='GET', renderer='json', permission='fetch_all')
def get_all_payments(request):
    # Returns all payments
    return request.db.query(Payment).order_by(Payment.created).all()
