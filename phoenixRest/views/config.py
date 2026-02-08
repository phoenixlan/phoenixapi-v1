from pyramid.view import view_config

from datetime import datetime
from datetime import timedelta

from pyramid.httpexceptions import (
    HTTPBadRequest,
    HTTPNotFound
)

from sqlalchemy import or_, and_

# For logging that appears in the debug toolbar
import logging
log = logging.getLogger(__name__)

# Rest api stuff

@view_config(name="config", renderer="json")
def server_config(request):
    """Returns the current configuration for the api server"""
    return {
        "name": request.registry.settings["api.name"],
        "logo": request.registry.settings["api.logo"],
        "contact": request.registry.settings["api.contact"],
    }
