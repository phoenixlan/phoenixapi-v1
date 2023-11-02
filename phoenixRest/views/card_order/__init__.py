from pyramid.authorization import Allow
from phoenixRest.roles import CHIEF, CREW_CARD_PRINTER, ADMIN

from pyramid.view import view_config
from phoenixRest.resource import resource
from phoenixRest.utils import validate

from phoenixRest.models.core.event import Event, get_current_event
from phoenixRest.models.core.user import User
from phoenixRest.models.core.avatar import Avatar, AvatarState
from phoenixRest.models.crew.card_order import CardOrder
from phoenixRest.views.card_order.instance import CardOrderInstanceResource

from sqlalchemy import and_

@resource(name="card_order")
class CardOrderResource(object):
    __acl__ = [
        # Roles with permission to create a new card order
         (Allow, CHIEF, "create"),
         (Allow, ADMIN, "create"),
        # Roles with permission to view all card orders for current event
         (Allow, CHIEF, "view_all"),
         (Allow, CREW_CARD_PRINTER, "view_all"),
         (Allow, ADMIN, "view_all"),
    ]   
         
    def __init__(self, request):
        self.request = request  
        
    def __getitem__(self, key):
        node = CardOrderInstanceResource(self.request, key)
        node.__parent__ = self
        node.__name__ = key
        return node

# Creates a new card order
@view_config(name="", context=CardOrderResource, request_method="POST", renderer="json", permission="create")
@validate(json_body={"user_uuid": str})
def create_card_order(context, request):
    current_event = get_current_event(request)
    if current_event is None:
        request.response.status = 400
        return {
            "error": "Current event not found"
        }
    
    subject_user_uuid = request.json_body["user_uuid"]
    subject_user = request.db.query(User).filter(User.uuid == subject_user_uuid).first()
    if subject_user is None:
        request.response.status = 400
        return {
            "error": "Subject user not found"
        }
    
    subject_has_avatar = request.db.query(Avatar).filter(and_(
        Avatar.user_uuid == subject_user_uuid,
        Avatar.state != AvatarState.rejected
    ))
    
    if subject_has_avatar is None:
        request.response.status = 400
        return {
            "error": "Subject user has no valid avatar"
        }
    
    creator_user = request.user
    
    card_order = CardOrder(current_event, subject_user, creator_user)
    request.db.add(card_order)
    request.db.flush()
    
    return card_order

# Get all card orders for specified or current event
@view_config(name="", context=CardOrderResource, request_method="GET", renderer="json", permission="view_all")
def get_card_orders(context, request):
    event = None
    # We either get the specified event or the current event
    if "event_uuid" in request.GET:
        event = request.db.query(Event).filter(Event.uuid == request.GET["event_uuid"]).first()
        if event is None:
            request.response.status = 400
            return {
                'error': "Event not found"
            }
    else:
        event = get_current_event(request)
    
    return request.db.query(CardOrder).filter(CardOrder.event_uuid == event.uuid).all()
