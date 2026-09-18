from phoenixRest.models.core.event import get_current_event, get_current_events

def test_get_current_event(db, upcoming_event, event_brand):
    """Tests get_current_event"""
    current_event = get_current_event(db, event_brand)
    assert current_event == upcoming_event
    
def test_get_current_events_no_event(db, event_brand):
    """Tests that if only the event_brand fixture is included, no event should exist in the system.
    This is mostly just a sanity check"""

    current_events = get_current_events(db)
    assert len(current_events) == 0

def test_get_current_events(db, upcoming_event):
    """Tests get_current_event"""
    current_events = get_current_events(db)

    current_event_uuids = list(map(lambda u: str(u), current_events))
    assert str(upcoming_event.uuid) in current_event_uuids

def test_get_current_events_returns_one_event_per_brand(
        db, upcoming_event, other_upcoming_event):
    current_events = set(get_current_events(db))

    assert current_events == {
        upcoming_event.uuid,
        other_upcoming_event.uuid
    }

        
def test_get_current_events_multiple_upcoming(db, upcoming_event, earlier_upcoming_event):
    """Test that if i create a more recent event, it will be the current one"""

    current_events = get_current_events(db)

    current_event_uuids = list(map(lambda u: str(u), current_events))
    assert str(earlier_upcoming_event.uuid) in current_event_uuids

def test_get_current_events_previous(db, upcoming_event, previous_event):
    """Test that previous events aren't included"""

    current_events = get_current_events(db)

    current_event_uuids = list(map(lambda u: str(u), current_events))
    assert str(upcoming_event.uuid) in current_event_uuids
