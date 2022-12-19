from ast import Pass
from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPNotFound,
    HTTPBadRequest
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow

from phoenixRest.models.core.password_reset_code import PasswordResetCode
from phoenixRest.models.core.oauth.refreshToken import OauthRefreshToken


from phoenixRest.utils import validate

from datetime import datetime, timedelta

import logging
log = logging.getLogger(__name__)

class PasswordResetCodeInstanceResource(object):
    def __acl__(self):
        return [
            (Allow, Everyone, 'get')
        ]

    def __init__(self, request, code):
        self.request = request
        log.info(code)
        self.resetCodeInstance = request.db.query(PasswordResetCode).filter(PasswordResetCode.code == code).first()

        if self.resetCodeInstance is None:
            raise HTTPNotFound("Not found")

@view_config(context=PasswordResetCodeInstanceResource, name='', request_method='GET', renderer='json', permission='get')
def get_password_reset_code(context, request):
    oldest_valid_time = datetime.now() - timedelta(hours=48)
    if context.resetCodeInstance.created < oldest_valid_time:
        request.response.status = 400
        return {
            'error': "Reset code has expired"
        }
    return context.resetCodeInstance


@view_config(context=PasswordResetCodeInstanceResource, name='', request_method='POST', renderer='json', permission='get')
@validate(json_body={'password': str, 'passwordRepeat': str})
def reset_password(context, request):
    oldest_valid_time = datetime.now() - timedelta(hours=48)
    if context.resetCodeInstance.created < oldest_valid_time:
        request.response.status = 400
        return {
            'error': "Reset code has expired"
        }
    password = request.json_body['password']
    password_repeat = request.json_body['passwordRepeat']
    if password != password_repeat:
        request.response.status = 400
        return {
            'error': 'Password and repeat password does not match'
        }
    context.resetCodeInstance.user.set_password(password)
    request.db.add(context.resetCodeInstance.user)

    # Delete all refresh tokens
    refresh_tokens = request.db.query(OauthRefreshToken).filter(OauthRefreshToken.user_uuid == context.resetCodeInstance.user.uuid).all()
    for token in refresh_tokens:
        request.db.delete(token)

    # Refresh the refresh code
    request.db.delete(context.resetCodeInstance)

    # Notify the user
    request.service_manager.get_service('email').send_mail(context.resetCodeInstance.user.email, "Passordet ditt har blitt tilbakestilt", "forgotten_notice.jinja2", {
        "mail": request.registry.settings["api.contact"],
        "name": request.registry.settings["api.name"],
        "domain": request.registry.settings["api.mainpage"]
    })

    return {
        'message': 'Password has been reset'
    }