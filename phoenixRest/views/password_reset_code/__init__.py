from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
)
from pyramid.security import Authenticated, Everyone, Deny, Allow

from phoenixRest.resource import resource


from phoenixRest.views.password_reset_code.instance import PasswordResetCodeInstanceResource

from datetime import datetime

import logging
log = logging.getLogger(__name__)

@resource(name='password_reset_code')
class PasswordResetCodeResource(object):
    __acl__ = [
        # Authenticated pages
        #(Allow, Authenticated, Authenticated),
        #(Deny, Everyone, Authenticated),
    ]
    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        """Traverse to a specific crew item"""
        log.info("Traverse")
        node = PasswordResetCodeInstanceResource(self.request, key)
        node.__parent__ = self
        node.__name__ = key
        return node

