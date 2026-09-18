
from phoenixRest.models.core.user import User

from phoenixRest.models.crew.permission import Permission
from phoenixRest.models.crew.position import Position
from phoenixRest.models.core.event_brand import EventBrand
from phoenixRest.models.crew.position_mapping import PositionMapping

import json
import base64
import pytest

def test_position_mapping_brand_sanity(testapp, db, upcoming_event, event_brand, jeff_user):
    """Check that if a mapping is assigned for an event that doesnt match the event brand of the position,
    the request fails"""
    current_user_dbobject = jeff_user

    # Create another event brand
    other_brand = EventBrand("Other brand!")
    db.add(other_brand)

    # Create two unique positions
    position_1 = Position("Test position 1", 'hehehe')
    position_1.event_brand = other_brand

    db.add(position_1)

    # Add test1 to current event position mapping
    # Note that upcoming_event is a different brand than EventBrand
    position_mapping= PositionMapping(current_user_dbobject, position_1, upcoming_event)

    db.add(position_mapping)

    # It shouldnt be possible to get a token
    with pytest.raises(ValueError):
        token, refresh = testapp.auth_get_tokens(jeff_user.email, 'sixcharacters')
        current_user = testapp.get('/user/current', headers=dict({
            'Authorization': "Bearer " + token
            }), status=500).json_body
