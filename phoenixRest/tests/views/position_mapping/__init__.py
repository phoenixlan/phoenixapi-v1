import json
import transaction

from phoenixRest.models.crew.position_mapping import PositionMapping

def test_create_delete_position_mapping(testapp, upcoming_event, admin_user, adam_user):
    # Log in as the test user
    token, refresh = testapp.auth_get_tokens(admin_user.email, 'sixcharacters')
    test_user_token, _ = testapp.auth_get_tokens(adam_user.email, 'sixcharacters')

    test_user = testapp.get_user(test_user_token)

    position_candidates = testapp.get('/position', headers=dict({
        "Authorization": "Bearer " + token
    }), status=200).json_body
    position_candidates = list(filter(
        lambda position: position['event_brand_uuid'] == str(upcoming_event.event_brand_uuid),
        position_candidates
    ))

    created_mapping = testapp.post_json('/event/%s/position_mapping' % upcoming_event.uuid, {
        "position_uuid": position_candidates[0]['uuid'],
        "user_uuid": test_user['uuid']
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
def test_no_permissionless_promotion(testapp, upcoming_event, admin_user, adam_user):
    # Log in as the test user
    token, refresh = testapp.auth_get_tokens(admin_user.email, 'sixcharacters')
    test_user_token, _ = testapp.auth_get_tokens(adam_user.email, 'sixcharacters')

    test_user = testapp.get_user(test_user_token)

    position_candidates = testapp.get('/position', headers=dict({
        "Authorization": "Bearer " + token
    }), status=200).json_body
    position_candidates = list(filter(
        lambda position: position['event_brand_uuid'] == str(upcoming_event.event_brand_uuid),
        position_candidates
    ))

    testapp.post_json('/event/%s/position_mapping' % upcoming_event.uuid, {
        "position_uuid": position_candidates[0]['uuid'],
        "user_uuid": test_user['uuid']
    }, headers=dict({
        "Authorization": "Bearer " + test_user_token
    }), status=403)

def test_hr_admin_mapping_permissions_and_brand_ownership(
        testapp, upcoming_event, other_upcoming_event, hr_admin_user,
        adam_user, brand_position, other_position):
    token, refresh = testapp.auth_get_tokens(hr_admin_user.email, 'sixcharacters')

    testapp.post_json('/event/%s/position_mapping' % upcoming_event.uuid, {
        'position_uuid': str(brand_position.uuid),
        'user_uuid': str(adam_user.uuid)
    }, headers={
        'Authorization': "Bearer " + token
    }, status=200)

    testapp.post_json('/event/%s/position_mapping' % other_upcoming_event.uuid, {
        'position_uuid': str(other_position.uuid),
        'user_uuid': str(adam_user.uuid)
    }, headers={
        'Authorization': "Bearer " + token
    }, status=403)

    response = testapp.post_json(
        '/event/%s/position_mapping' % upcoming_event.uuid,
        {
            'position_uuid': str(other_position.uuid),
            'user_uuid': str(adam_user.uuid)
        },
        headers={'Authorization': "Bearer " + token},
        status=400
    )
    assert response.json_body['error'] == \
        'Position belongs to a different event brand'
