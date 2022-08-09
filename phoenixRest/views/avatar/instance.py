from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPNotFound,
    HTTPBadRequest
)
from pyramid.security import Authenticated, Everyone, Deny, Allow

from phoenixRest.models import db
from phoenixRest.models.core.avatar import Avatar, AvatarState

from phoenixRest.mappers.crew import map_crew

from phoenixRest.roles import ADMIN, HR_ADMIN

from phoenixRest.utils import validate
from phoenixRest.resource import resource

from datetime import datetime
import os

import logging
log = logging.getLogger(__name__)

from PIL import Image

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
        (Allow, HR_ADMIN, 'avatar_update'),
        (Allow, ADMIN, 'avatar_update')

        # Authenticated pages
        #(Allow, Authenticated, Authenticated),
        #(Deny, Everyone, Authenticated),
    ]

    def __init__(self, request, uuid):
        self.request = request
        self.avatarInstance = db.query(Avatar).filter(Avatar.uuid == uuid).first()

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

    db.delete(context.avatarInstance)
    return 'ok'

@view_config(context=AvatarInstanceResource, name='', request_method='PATCH', renderer='string', permission='avatar_update')
@validate(json_body={'new_state': str})
def update_status(context, request):
    if request.json_body['new_state'] not in ['accepted', 'rejected']:
        raise HTTPBadRequest('new state is not accepted or rejected')
    if context.avatarInstance.state != AvatarState.uploaded:
        raise HTTPBadRequest('Avatar is already accepted or rejected')

    enum = AvatarState[request.json_body['new_state']]
    if enum is None:
        raise HTTPBadRequest('uh i fucked up')

    # TODO send email if avatar is accepted

    context.avatarInstance.state = enum
    db.add(context.avatarInstance)
    return 'ok'