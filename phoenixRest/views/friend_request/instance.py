from pyramid.view import view_config, view_defaults

from pyramid.httpexceptions import HTTPNotFound

from phoenixRest.models.core.friendship import Friendship

from phoenixRest.utils import validateUuidAndQuery
from phoenixRest.utils import validate

from sqlalchemy import and_, or_, extract

from datetime import datetime

class FriendRequestInstanceResource(object):
    def __acl__(self):
        acl = [
            
        ]
    def __init__(self, request, uuid):
        self.request = request
        
        self.friendRequestInstance = validateUuidAndQuery(request, Friendship, Friendship.uuid, uuid)
        if self.friendRequestInstance == None:
            raise HTTPNotFound("friend_request with specified uuid not found")
        
@view_config(name="", context=FriendRequestInstanceResource, request_method="GET", renderer="json", permission="")
def view_friendship(context, request):
    return context.friendRequestInstance

@view_config(name="", context=FriendRequestInstanceResource, request_method="DELETE", renderer="json", permission="")
def revoke_friendship(context, request):
    if context.friendRequestInstance.revoked is not None:
        request.status = 400
        return {
            "error": "friendship already revoked"
        }
        
    context.friendRequestInstance.revoked = datetime.now()
    
    return context.friendRequestInstance

@view_config(name="", context=FriendRequestInstanceResource, request_method="POST", renderer="json", permission="")
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
