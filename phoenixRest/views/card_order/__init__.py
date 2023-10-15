from pyramid.view import view_config
from pyramid.authorization import Allow

from phoenixRest.resource import resource
from phoenixRest.utils import validate
from phoenixRest.roles import CHIEF, CREW_CARD_PRINTER

from phoenixRest.models.core.user import User

from phoenixRest.models.crew.card_order import CardOrder
from phoenixRest.views.card_order.instance import CardOrderInstanceResource

@resource(name="card_order")
class CardOrderResource(object):
    __acl__ = [
         (Allow, CHIEF, "create"),
         
         (Allow, CHIEF, "view_all"),
         (Allow, CREW_CARD_PRINTER, "view_all"),
    ]   
         
    def __init__(self, request):
        self.request = request  
        
    def __getitem__(self, key):
        node = CardOrderInstanceResource(self.request, key)
        node.__parent__ = self
        node.__name__ = key
        return node
    
from phoenixRest.models.core.event import get_current_event

# Creates a new card order
@view_config(name="", context=CardOrderResource, request_method="POST", renderer="json", permission="create")
@validate(json_body={"user_uuid": str})
def create_card_order(context, request):
    current_event = get_current_event(request)
    if current_event is None:
        request.status = 400
        return {
            "error": "Current event not found"
        }
    
    subject_user_uuid = request.json_body["user_uuid"]
    subject_user = request.db.query(User).filter(User.uuid == subject_user_uuid).first()
    if subject_user is None:
        request.status = 400
        return {
            "error": "Subject user not found"
        }
    
    creator_user = request.user
    
    card_order = CardOrder(current_event, subject_user, creator_user)
    request.db.add(card_order)
    request.db.flush()
    
    return card_order

# Get all card orders for current event
@view_config(name="", context=CardOrderResource, request_method="GET", renderer="json", permission="view_all")
def get_card_orders(context, request):
    current_card_orders = request.db.query(CardOrder).filter(CardOrder.event == get_current_event(request))
    return current_card_orders
