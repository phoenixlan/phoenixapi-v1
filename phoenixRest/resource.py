from pyramid.security import Authenticated, Everyone, Deny, Allow

import logging
log = logging.getLogger(__name__)

class RootResource(object):
    nodes = {}
    """Root traversal node used for permissions stuff"""
    # (Action, Principal, Permission
    __acl__ = [
        # Authenticated pages
        #(Allow, Authenticated, Authenticated),
        #(Deny, Everyone, Authenticated)

        (Allow, Everyone, 'auth')
        #(Allow, Everyone, 'event::current::get'),
        #(Allow, 'Admin', 'event.manage'),
    ]

    def __init__(self, request):
        """Set up ACL for this request"""
        self.request = request

    @classmethod
    def add_node(cls, name, obj):
        """Add a child to the root node"""
        cls.nodes[name] = obj

    def __getitem__(self, key):
        """Look up a traversal node"""
        log.debug("TRAVERSE: TRYING TO FIND %s" % key)
        node = self.nodes[key](self.request)
        node.__parent__ = self
        node.__name__ = key
        return node

def resource(name: str):
    global _resources
    def resource_inner(cl):
        log.debug("Registered resource %s" % name)
        RootResource.add_node(name, cl)
        return cl
    return resource_inner

