from pyramid.view import view_config, view_defaults

from phoenixRest.models.core.friendship import Friendship

from pyramid.httpexceptions import HTTPNotFound

from phoenixRest.utils import validateUuidAndQuery
from phoenixRest.utils import validate

from sqlalchemy import and_, or_, extract

class FriendRequestInstanceResource(object):
    def __acl__(self):
        acl = [
            
        ]
    def __init(self, request, uuid):
        self.request = request
        
        self.friendRequestInstance = validateUuidAndQuery(request, Friendship, Friendship.uuid, uuid)
        if self.friendRequestInstance == None:
            raise HTTPNotFound("User not found")    
        
@view_config(name="", context=FriendRequestInstanceResource, request_method="GET", renderer="json", permission="")
def view_friendship(context, request):
    friendship = request.db.query(Friendship).filter()
    #? Do what now ?#

@view_config(name="", context=FriendRequestInstanceResource, request_method="DELETE", renderer="json", permission="")
def delete_friendship(context, request):
    friendship = request.db.query(Friendship).filter(context.friendRequestInstance == )
    if friendship == None:      

@view_config(name="", context=FriendRequestInstanceResource, request_method="POST", renderer="json", permission="")
def accept(context, request):
    friendship = request.db.query(Friendship).filter()
    