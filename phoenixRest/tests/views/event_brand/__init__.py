
def test_event_brand_create_and_list(testapp, db, admin_user):
    """Test creating and listing event brands"""
    # Admin token is required for creating brands
    token, refresh = testapp.auth_get_tokens(admin_user.email, 'sixcharacters')

    # List event brands - should be empty initially
    res = testapp.get('/event_brand', status=200)
    initial_count = len(res.json_body)

    # Create a new event brand
    res = testapp.post_json('/event_brand', {
        'name': 'Test Brand'
    }, headers={
        "Authorization": "Bearer " + token
    }, status=200)

    # Verify the response
    assert res.json_body['name'] == 'Test Brand'
    assert 'uuid' in res.json_body
    brand_uuid = res.json_body['uuid']

    # List event brands again - should now have one more brand
    res = testapp.get('/event_brand', status=200)
    assert len(res.json_body) == initial_count + 1
    assert any(b['name'] == 'Test Brand' for b in res.json_body)

    # Fetch the created brand using the instance endpoint
    res = testapp.get('/event_brand/%s' % brand_uuid, status=200)
    assert res.json_body['uuid'] == brand_uuid
    assert res.json_body['name'] == 'Test Brand'


def test_create_ticket_type_for_brand(testapp, event_brand, admin_token):
    ticket_type = testapp.post_json(
        '/event_brand/%s/ticket_type' % event_brand.uuid,
        {
            'name': 'Brand ticket',
            'price': 250,
            'description': 'A tenant-owned ticket type',
            'refundable': True,
            'seatable': False,
            'grants_admission': True
        },
        headers={'Authorization': "Bearer " + admin_token},
        status=200
    ).json_body

    assert ticket_type['name'] == 'Brand ticket'
    assert ticket_type['price'] == 250
    assert ticket_type['description'] == 'A tenant-owned ticket type'
    assert ticket_type['refundable'] is True
    assert ticket_type['seatable'] is False
    assert ticket_type['grants_admission'] is True
    assert ticket_type['event_brand_uuid'] == str(event_brand.uuid)


def test_positions_are_listed_only_for_their_event_brand(
        testapp, event_brand, other_event_brand, brand_position,
        other_position, admin_token):
    headers = {'Authorization': "Bearer " + admin_token}

    brand_positions = testapp.get(
        '/event_brand/%s/positions' % event_brand.uuid,
        headers=headers,
        status=200
    ).json_body
    other_brand_positions = testapp.get(
        '/event_brand/%s/positions' % other_event_brand.uuid,
        headers=headers,
        status=200
    ).json_body

    brand_position_uuids = {
        position['uuid'] for position in brand_positions
    }
    other_brand_position_uuids = {
        position['uuid'] for position in other_brand_positions
    }

    assert str(brand_position.uuid) in brand_position_uuids
    assert str(other_position.uuid) not in brand_position_uuids
    assert {
        position['event_brand_uuid'] for position in brand_positions
    } == {str(event_brand.uuid)}

    assert str(other_position.uuid) in other_brand_position_uuids
    assert str(brand_position.uuid) not in other_brand_position_uuids
    assert {
        position['event_brand_uuid'] for position in other_brand_positions
    } == {str(other_event_brand.uuid)}


def test_crews_are_listed_only_for_their_event_brand(
        testapp, event_brand, other_event_brand, testcrew, other_crew,
        admin_token):
    headers = {'Authorization': "Bearer " + admin_token}

    brand_crews = testapp.get(
        '/event_brand/%s/crews' % event_brand.uuid,
        headers=headers,
        status=200
    ).json_body
    other_brand_crews = testapp.get(
        '/event_brand/%s/crews' % other_event_brand.uuid,
        headers=headers,
        status=200
    ).json_body

    assert {crew['uuid'] for crew in brand_crews} == {str(testcrew.uuid)}
    assert {crew['uuid'] for crew in other_brand_crews} == {
        str(other_crew.uuid)
    }


def test_get_current_event_for_brand(testapp, event_brand, upcoming_event):
    """Test getting the current event for a specific brand"""
    res = testapp.get('/event_brand/%s/current_event' % str(event_brand.uuid), status=200)
    assert res.json_body is not None
    assert res.json_body['name'] == upcoming_event.name
    assert res.json_body['uuid'] == str(upcoming_event.uuid)
    assert res.json_body['event_brand_uuid'] == str(event_brand.uuid)


def test_get_current_event_no_events(testapp, event_brand):
    """Test getting current event when brand has no events"""
    # Should return null when there are no events
    res = testapp.get('/event_brand/%s/current_event' % str(event_brand.uuid), status=200)
    assert res.json_body is None


def test_get_current_event_only_past_events(testapp, event_brand, previous_event):
    """Test getting current event when brand only has past events"""
    # Should return null when there are only past events
    res = testapp.get('/event_brand/%s/current_event' % str(event_brand.uuid), status=200)
    assert res.json_body is None


def test_get_current_event_multiple_upcoming(testapp, event_brand, upcoming_event, earlier_upcoming_event):
    """Test getting current event when brand has multiple upcoming events - should return earliest"""
    # Should return the earliest upcoming event
    res = testapp.get('/event_brand/%s/current_event' % str(event_brand.uuid), status=200)
    assert res.json_body is not None
    assert res.json_body['name'] == earlier_upcoming_event.name
    assert res.json_body['uuid'] == str(earlier_upcoming_event.uuid)
