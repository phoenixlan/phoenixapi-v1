from pyramid.view import view_config, view_defaults

from phoenixRest.models.core.user import User
from phoenixRest.models.core.friendship import Friendship

from phoenixRest.utils import validate
from phoenixRest.resource import resource

from sqlalchemy import and_, or_, extract, null

@resource(name='friend_request')
class FriendRequestResource(object):
    def __acl__(self):
        acl = [
            
        ]
    def __init__(self, request):
        self.request = request
    """      
    def __getitem__(self, key):
        node = TicketVoucherInstanceResource(self.request, key)
        node.__parent__ = self
        node.__name__ = key
        return node
    """

@view_config(name="", context=FriendRequestResource, request_method="POST", renderer="json", permission="")
@validate(json_body={"user_email": str})
def create_friend_request(context, request):
    recipient_user_email = request.json_body["user_email"]
    recipient_user = request.db.query(User).filter(User.email == recipient_user_email).first()
    if not recipient_user:
        request.response.status = 404
        return {
            "error": "recipient_user not found"
        }
    
    has_active_friendship = request.db.query(Friendship).filter(
        and_(
            Friendship.revoked is not None, #? V
            and_(Friendship.source_user == request.user, Friendship.recipient_user == recipient_user)
        )
    )
    if has_active_friendship:
        request.status = 400
        return {
            "error": "user already has friendship with recipient_user"
        }
                                  #? V
    friend_request = Friendship(request.user, recipient_user, None, None)
    
    request.db.add(friend_request)
    request.db.flush()
    
    return friend_request
