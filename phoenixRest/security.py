from pyramid.httpexceptions import (
	HTTPUnauthorized,
	HTTPOk
)

from phoenixRest.models import db, Base
from phoenixRest.models.core.user import User

import logging
import os

log = logging.getLogger(__name__)

