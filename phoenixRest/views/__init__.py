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

@view_config(route_name="home", renderer="string")
def home(request):
    return "hello"
