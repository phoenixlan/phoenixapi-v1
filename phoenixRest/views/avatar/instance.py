from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPNotFound,
    HTTPBadRequest
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow

from phoenixRest.models.core.avatar import Avatar, AvatarState

from phoenixRest.roles import ADMIN, HR_ADMIN, CHIEF

from phoenixRest.utils import validate
import os

import logging
log = logging.getLogger(__name__)

class AvatarInstanceResource(object):
    def __acl__(self):
        return [
        (Allow, HR_ADMIN, 'avatar_view'),
        (Allow, ADMIN, 'avatar_view'),
        (Allow, 'role:user:%s' % self.avatarInstance.user.uuid, 'avatar_view'),

        (Allow, HR_ADMIN, 'avatar_delete'),
        (Allow, ADMIN, 'avatar_delete'),
        (Allow, 'role:user:%s' % self.avatarInstance.user.uuid, 'avatar_delete'),

        # Only admins can update avatar state
        # And chiefs. Chiefs do most HR work for their crew
        (Allow, HR_ADMIN, 'avatar_update'),
        (Allow, CHIEF, 'avatar_update'),
        (Allow, ADMIN, 'avatar_update')

        # Authenticated pages
        #(Allow, Authenticated, Authenticated),
        #(Deny, Everyone, Authenticated),
    ]

    def __init__(self, request, uuid):
        self.request = request
        self.avatarInstance = request.db.query(Avatar).filter(Avatar.uuid == uuid).first()

        if self.avatarInstance is None:
            raise HTTPNotFound("Avatar not found")

@view_config(context=AvatarInstanceResource, name='', request_method='GET', renderer='json', permission='avatar_view')
def get_avatar(context, request):
    return context.avatarInstance
    
@view_config(context=AvatarInstanceResource, name='', request_method='DELETE', renderer='string', permission='avatar_delete')
def delete_avatar(context, request):
    avatar_thumb_dir = request.registry.settings["avatar.directory_thumb"]
    avatar_sd_dir = request.registry.settings["avatar.directory_sd"]
    avatar_hd_dir = request.registry.settings["avatar.directory_hd"]

    os.remove(os.path.join(avatar_thumb_dir, "%s.%s" % (context.avatarInstance.uuid, context.avatarInstance.extension)))
    os.remove(os.path.join(avatar_sd_dir, "%s.%s" % (context.avatarInstance.uuid, context.avatarInstance.extension)))
    os.remove(os.path.join(avatar_hd_dir, "%s.%s" % (context.avatarInstance.uuid, context.avatarInstance.extension)))

    request.db.delete(context.avatarInstance)
    return 'ok'

@view_config(context=AvatarInstanceResource, name='', request_method='PATCH', renderer='string', permission='avatar_update')
@validate(json_body={'new_state': str})
def update_status(context, request):
    if request.json_body['new_state'] not in ['accepted', 'rejected']:
        request.response.status = 400
        return {
            "error": "New avatar state is not accepted or rejected"
        }
    if context.avatarInstance.state != AvatarState.uploaded:
        request.response.status = 400
        return {
            "error": "Avatar is already accepted or rejected"
        }

    enumerated_state = AvatarState[request.json_body['new_state']]
    if enumerated_state is None:
        raise HTTPBadRequest('uh i fucked up')

    title = "Avataren ble avslått"
    if enumerated_state == AvatarState.accepted:
        title = "Avataren ble godkjent"

    request.service_manager.get_service('email').send_mail(context.avatarInstance.user.email, title, "avatar_state_changed.jinja2", {
        "mail": request.registry.settings["api.contact"],
        "accepted": enumerated_state == AvatarState.accepted,
        "name": request.registry.settings["api.name"],
        "domain": request.registry.settings["api.mainpage"]
    })

    context.avatarInstance.state = enumerated_state
    request.db.add(context.avatarInstance)
    return 'ok'