from phoenixRest.models.core.event_brand import EventBrand
from phoenixRest.models.core.event import Event
from datetime import datetime, timedelta


def test_event_brand_create_and_list(testapp, db):
    """Test creating and listing event brands"""
    # Admin token is required for creating brands
    token, refresh = testapp.auth_get_tokens('test@example.com', 'sixcharacters')

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


def test_get_current_event_for_brand(testapp, db):
    """Test getting the current event for a specific brand"""
    # Create a brand
    brand = EventBrand("Test Brand")
    db.add(brand)
    db.flush()

    # Create an upcoming event for this brand
    event_start = datetime.now() + timedelta(days=10)
    event_end = datetime.now() + timedelta(days=13)
    event = Event("Test Event for Brand", event_start, event_end, 400, brand)
    db.add(event)
    db.flush()

    # Get the current event for this brand
    res = testapp.get('/event_brand/%s/current_event' % str(brand.uuid), status=200)
    assert res.json_body is not None
    assert res.json_body['name'] == 'Test Event for Brand'
    assert res.json_body['uuid'] == str(event.uuid)
    assert res.json_body['event_brand_uuid'] == str(brand.uuid)


def test_get_current_event_no_events(testapp, db):
    """Test getting current event when brand has no events"""
    # Create a brand with no events
    brand = EventBrand("Empty Brand")
    db.add(brand)
    db.flush()

    # Should return null when there are no events
    res = testapp.get('/event_brand/%s/current_event' % str(brand.uuid), status=200)
    assert res.json_body is None


def test_get_current_event_only_past_events(testapp, db):
    """Test getting current event when brand only has past events"""
    # Create a brand
    brand = EventBrand("Past Events Brand")
    db.add(brand)
    db.flush()

    # Create a past event
    event_start = datetime.now() - timedelta(days=30)
    event_end = datetime.now() - timedelta(days=27)
    event = Event("Past Event", event_start, event_end, 400, brand)
    db.add(event)
    db.flush()

    # Should return null when there are only past events
    res = testapp.get('/event_brand/%s/current_event' % str(brand.uuid), status=200)
    assert res.json_body is None


def test_get_current_event_multiple_upcoming(testapp, db):
    """Test getting current event when brand has multiple upcoming events - should return earliest"""
    # Create a brand
    brand = EventBrand("Multiple Events Brand")
    db.add(brand)

    # Create multiple upcoming events
    event1_start = datetime.now() + timedelta(days=20)
    event1_end = datetime.now() + timedelta(days=23)
    event1 = Event("Later Event", event1_start, event1_end, 400, brand)
    db.add(event1)

    event2_start = datetime.now() + timedelta(days=10)
    event2_end = datetime.now() + timedelta(days=13)
    event2 = Event("Earlier Event", event2_start, event2_end, 400, brand)
    db.add(event2)
    db.flush()

    # Should return the earliest upcoming event
    res = testapp.get('/event_brand/%s/current_event' % str(brand.uuid), status=200)
    assert res.json_body is not None
    assert res.json_body['name'] == 'Earlier Event'
    assert res.json_body['uuid'] == str(event2.uuid)
