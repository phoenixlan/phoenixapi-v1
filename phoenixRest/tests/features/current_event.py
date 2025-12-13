from phoenixRest.models.core.event import get_current_event, get_current_events, Event

from datetime import datetime, timedelta

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

        
def test_get_current_events_multiple_upcoming(db, upcoming_event, event_brand):
    """Test that if i create a more recent event, it will be the current one"""

    earlier_event = Event("Earlier event", datetime.now() + timedelta(days=20), datetime.now() + timedelta(days=22), 400, event_brand)
    earlier_event.booking_time = datetime.now() + timedelta(days=2)
    earlier_event.seating_time_delta = 30
    db.add(earlier_event)
    db.flush()

    
    current_events = get_current_events(db)

    current_event_uuids = list(map(lambda u: str(u), current_events))
    assert str(earlier_event.uuid) in current_event_uuids

def test_get_current_events_previous(db, upcoming_event, event_brand):
    """Test that previous events aren't included"""
    
    earlier_event = Event("Earlier event", datetime.now() - timedelta(days=20), datetime.now() - timedelta(days=22), 400, event_brand)
    earlier_event.booking_time = datetime.now() + timedelta(days=2)
    earlier_event.seating_time_delta = 30
    db.add(earlier_event)
    db.flush()

    
    current_events = get_current_events(db)

    current_event_uuids = list(map(lambda u: str(u), current_events))
    assert str(upcoming_event.uuid) in current_event_uuids