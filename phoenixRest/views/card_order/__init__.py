from phoenixRest.resource import resource
from phoenixRest.views.card_order.instance import CardOrderInstanceResource

@resource(name="card_order")
class CardOrderResource(object):
    __acl__ = []
         
    def __init__(self, request):
        self.request = request  
        
    def __getitem__(self, key):
        node = CardOrderInstanceResource(self.request, key)
        node.__parent__ = self
        node.__name__ = key
        return node
