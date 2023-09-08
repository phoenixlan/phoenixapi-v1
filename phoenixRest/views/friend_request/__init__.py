from pyramid.view import view_config, view_defaults

from pyramid.authorization import Allow, Authenticated

from phoenixRest.models.core.user import User
from phoenixRest.models.core.friendship import Friendship
from phoenixRest.views.friend_request.instance import FriendRequestInstanceResource

from phoenixRest.utils import validate
from phoenixRest.resource import resource

from sqlalchemy import and_, or_, extract, null

@resource(name='friend_request')
class FriendRequestResource(object):
    __acl__ = [
        (Allow, Authenticated, 'create'),
    ]   
         
    def __init__(self, request):
        self.request = request  
        
    def __getitem__(self, key):
        node = FriendRequestInstanceResource(self.request, key)
        node.__parent__ = self
        node.__name__ = key
        return node

@view_config(name="", context=FriendRequestResource, request_method="POST", renderer="json", permission="create")
@validate(json_body={"user_email": str})
def create_friend_request(context, request):
    recipient_user_email = request.json_body["user_email"].lower()
    recipient_user = request.db.query(User).filter(User.email == recipient_user_email).first()
    if not recipient_user:
        request.response.status = 400
        return {
            "error": "User not found"
        }
    
    has_active_friendship = request.db.query(Friendship).filter(
        and_(Friendship.source_user == request.user, Friendship.recipient_user == recipient_user)
    ).first()
    if has_active_friendship:
        request.status = 400
        return {
            "error": "You are already friends with this user!"
        }
        
    friend_request = Friendship(request.user, recipient_user)
    
    request.db.add(friend_request)
    request.db.flush()
    
    return friend_request
