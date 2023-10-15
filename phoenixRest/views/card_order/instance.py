from pyramid.authorization import Allow
from pyramid.httpexceptions import HTTPNotFound

from phoenixRest.roles import CREW_CARD_PRINTER, CHIEF, ADMIN
from phoenixRest.utils import validateUuidAndQuery
from phoenixRest.models.crew.card_order import CardOrder, OrderStates

class CardOrderInstanceResource(object):
    def __acl__(self):
        acl = [
            # Roles with permission to view the card order
            (Allow, CREW_CARD_PRINTER, "view"),
            (Allow, CHIEF, "view"),
            (Allow, ADMIN, "view"),
            # Roles with permission to generate a crew card based on an order
            (Allow, CREW_CARD_PRINTER, "print"),
            (Allow, ADMIN, "print"),
            # Roles with permission to cancel the card order
            (Allow, CHIEF, "cancel"),
            (Allow, ADMIN, "cancel"),
        ]
        return acl
    
    def __init__(self, request, uuid):
        self.request = request
        
        self.cardOrderInstance = validateUuidAndQuery(request, CardOrder, CardOrder.uuid, uuid)
        if self.cardOrderInstance == None:
            raise HTTPNotFound("card_order with specified uuid not found")

from pyramid.view import view_config

from datetime import datetime
from phoenixRest.features.crew_card import generate_badge
from phoenixRest.models.core.event import get_current_event

# Views the specified card order
@view_config(name="", context=CardOrderInstanceResource, request_method="GET", renderer="json", permission="view")
def view_card_order(context, request):
    return context.cardOrderInstance

# Generates a crew card and updates the state of the order
@view_config(name="generate", context=CardOrderInstanceResource, request_method="PATCH", renderer="pillow", permission="print")
def generate_crew_card_from_order(context, request):
    if context.cardOrderInstance.state == OrderStates.CANCELLED.value:
        request.response.status = 403
        return {
            "error": "This order is cancelled, cannot generate"
        }
        
    context.cardOrderInstance.state = OrderStates.IN_PROGRESS.value
    context.cardOrderInstance.last_updated = datetime.now()
    context.cardOrderInstance.updated_by_user = request.user
    
    return generate_badge(request, context.cardOrderInstance.subject_user, get_current_event(request))

# Marks the order as finished
@view_config(name="finish", context=CardOrderInstanceResource, request_method="PATCH", renderer="json", permission="print")
def finish_card_order(context, request):
    context.cardOrderInstance.state = OrderStates.FINISHED.value
    context.cardOrderInstance.last_updated = datetime.now()
    context.cardOrderInstance.updated_by_user = request.user
    
    return context.cardOrderInstance

# Marks the order as cancelled
@view_config(name="cancel", context=CardOrderInstanceResource, request_method="DELTE", renderer="json", permission="cancel")
def cancel_card_order(context, request):
    context.cardOrderInstance.state = OrderStates.CANCELLED.value
    context.cardOrderInstance.last_updated = datetime.now()
    context.cardOrderInstance.updated_by_user = request.user
    
    return context.cardOrderInstance
