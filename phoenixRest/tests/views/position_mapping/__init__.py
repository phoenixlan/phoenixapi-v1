import json
import transaction

from phoenixRest.models.crew.position_mapping import PositionMapping

def test_create_delete_position_mapping(testapp, upcoming_event):
    # Log in as the test user
    token, refresh = testapp.auth_get_tokens('test@example.com', 'sixcharacters')
    test_user_token, _ = testapp.auth_get_tokens('adam@example.com', 'sixcharacters')

    test_user = testapp.get_user(test_user_token)

    position_candidates = testapp.get('/position', headers=dict({
        "Authorization": "Bearer " + token
    }), status=200).json_body

    created_mapping = testapp.post_json('/position_mapping', {
        "position_uuid": position_candidates[0]['uuid'],
        "user_uuid": test_user['uuid'],
        "event_uuid": str(upcoming_event.uuid)
    }, headers=dict({
        "Authorization": "Bearer " + token
    }), status=200).json_body

    assert created_mapping['uuid'] != None

    # Assure the position mapping actually exists
    test_user = testapp.get_user(test_user_token)

    exists = False
    for position_mapping in test_user['position_mappings']:
        if position_mapping['uuid'] == created_mapping['uuid']:
            exists = True
    
    assert exists

    # Try fetching it
    position_mapping_fetched = testapp.get('/position_mapping/%s' % created_mapping['uuid'], headers=dict({
        "Authorization": "Bearer " + token
    }), status=200).json_body

    assert position_mapping_fetched['uuid'] == created_mapping['uuid']

    # Now delete it
    testapp.delete('/position_mapping/%s' % created_mapping['uuid'], headers=dict({
        "Authorization": "Bearer " + token
    }), status=200)

    # Fetching it should now result in 404
    testapp.get('/position_mapping/%s' % created_mapping['uuid'], headers=dict({
        "Authorization": "Bearer " + token
    }), status=404)
    
# Make sure a permissionless user can't make permission mappings. Low-hanging fruit to test
def test_no_permissionless_promotion(testapp, upcoming_event):
    # Log in as the test user
    token, refresh = testapp.auth_get_tokens('test@example.com', 'sixcharacters')
    test_user_token, _ = testapp.auth_get_tokens('adam@example.com', 'sixcharacters')

    test_user = testapp.get_user(test_user_token)

    position_candidates = testapp.get('/position', headers=dict({
        "Authorization": "Bearer " + token
    }), status=200).json_body

    testapp.post_json('/position_mapping', {
        "position_uuid": position_candidates[0]['uuid'],
        "user_uuid": test_user['uuid'],
        "event_uuid": str(upcoming_event.uuid)
    }, headers=dict({
        "Authorization": "Bearer " + test_user_token
    }), status=403)
