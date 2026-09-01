from pyramid.view import notfound_view_config, view_config, exception_view_config
from pyramid.response import Response
from pyramid.request import Request
import logging
import traceback
import json

import pyramid.httpexceptions as exc


@view_config(context=exc.HTTPForbidden, renderer="json")
def error_forbidden(exc, request: Request):
    request.response.status_code = 403
    return {
        "error": "403 Forbidden"
    }