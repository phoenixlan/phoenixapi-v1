from phoenixRest.models.core.user import User

from phoenixRest.models.crew.permission import Permission
from phoenixRest.models.crew.position import Position
from phoenixRest.models.crew.position_mapping import PositionMapping

import json
import base64

# Tests that roles are correctly given out depending on current event
def test_role_event_assignment(testapp, db, upcoming_event):
    last_event = testapp.get_last_event(db)
    current_event = testapp.get_current_event(db)

    current_user_dbobject = db.query(User).filter(User.username == 'jeff').first()

    # Create two unique positions
    position_1 = Position("Test position 1", 'hehehe')
    position_2 = Position("Test position 2", 'hehehe')

    # Create two unique permissions
    permission_1 = Permission(position_1, 'test1', None)
    permission_2 = Permission(position_2, 'test2', None)

    db.add(permission_1)
    db.add(permission_2)

    # Add test1 to current event position mapping
    position_mapping_now = PositionMapping(current_user_dbobject, position_1, current_event)
    position_mapping_past = PositionMapping(current_user_dbobject, position_2, last_event)

    db.add(position_mapping_now)
    db.add(position_mapping_past)

    # Now log in and check what permissions we have
    token, refresh = testapp.auth_get_tokens('jeff@example.com', 'sixcharacters')
    current_user = testapp.get('/user/current', headers=dict({
        'Authorization': "Bearer " + token
        }), status=200).json_body
    
    # First ensure that position mappings show up properly
    current_mappings = list(filter(lambda mapping: mapping['event_uuid'] == str(current_event.uuid), current_user['position_mappings']))
    assert len(current_mappings) == 1
    last_mappings = list(filter(lambda mapping: mapping['event_uuid'] == str(last_event.uuid), current_user['position_mappings']))
    assert len(last_mappings) == 1

    # Now parse the jwt token we got
    token_payload = json.loads(base64.b64decode(token.split(".")[1]+"=="))

    # Did we have the expected roles?
    expected_roles = ['user:%s' % current_user['uuid'], 'test1', 'member']

    assert sorted(token_payload['roles']) == sorted(expected_roles)