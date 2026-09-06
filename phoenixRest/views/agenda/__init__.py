from pyramid.view import view_config, view_defaults
from pyramid.authorization import Authenticated, Everyone, Deny, Allow

from phoenixRest.models.core.agenda_entry import AgendaEntry
from phoenixRest.models.core.event import Event, get_current_event

from phoenixRest.utils import validate
from phoenixRest.resource import resource

from phoenixRest.roles import ADMIN, BRAND_ADMIN, COMPO_ADMIN, INFO_ADMIN

from phoenixRest.views.agenda.instance import AgendaInstanceResource

from datetime import datetime

import logging
log = logging.getLogger(__name__)


@view_defaults(context='.AgendaViews')
@resource(name='agenda')
class AgendaViews(object):
    __acl__ = [
        (Allow, ADMIN(), 'create')
    ]
    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        node = AgendaInstanceResource(self.request, key)
        node.__parent__ = self
        node.__name__ = key
        return node
