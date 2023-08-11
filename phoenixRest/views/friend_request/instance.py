from pyramid.view import view_config, view_defaults

from pyramid.httpexceptions import HTTPNotFound

from pyramid.authorization import Allow, Deny
from phoenixRest.roles import ADMIN

from phoenixRest.models.core.friendship import Friendship

from phoenixRest.utils import validateUuidAndQuery
from phoenixRest.utils import validate

from sqlalchemy import and_, or_, extract

from datetime import datetime

class FriendRequestInstanceResource(object):
    def __acl__(self):
        source_user_uuid = self.friendRequestInstance.source_user.uuid
        recipient_user_uuid = self.friendRequestInstance.recipient_user.uuid
        acl = [
            (Allow, ADMIN, "view")
            (Allow, f"{source_user_uuid}", "view"),
            (Allow, f"{recipient_user_uuid}", "view"),
            
            (Allow, ADMIN, "revoke")
            (Allow, f"{source_user_uuid}", "revoke"),
            (Allow, f"{recipient_user_uuid}", "revoke"),
            
            (Allow, ADMIN, "accept")
            (Deny, f"{source_user_uuid}", "accept"),
            (Allow, f"{recipient_user_uuid}", "accept"),
            
            
        ]
    def __init__(self, request, uuid):
        self.request = request
        
        self.friendRequestInstance = validateUuidAndQuery(request, Friendship, Friendship.uuid, uuid)
        if self.friendRequestInstance == None:
            raise HTTPNotFound("friend_request with specified uuid not found")
        
@view_config(name="", context=FriendRequestInstanceResource, request_method="GET", renderer="json", permission="view")
def view_friendship(context, request):
    return context.friendRequestInstance

@view_config(name="", context=FriendRequestInstanceResource, request_method="DELETE", renderer="json", permission="revoke")
def revoke_friendship(context, request):
    if context.friendRequestInstance.revoked is not None:
        request.status = 400
        return {
            "error": "friendship already revoked"
        }
        
    context.friendRequestInstance.revoked = datetime.now()
    
    return context.friendRequestInstance

@view_config(name="", context=FriendRequestInstanceResource, request_method="POST", renderer="json", permission="accept")
def accept_friendship(context, request):
    if context.friendRequestInstance.revoked is not None:
        request.status = 400
        return {
            "error": "friend_request already revoked, cannot accept"
        }
    elif context.friendRequestInstance.accepted is not None:
        request.status = 400
        return {
            "error": "friend_request already accepted"
        }
    
    context.friendRequestInstance.accepted = datetime.now()
    return context.friendRequestInstance
