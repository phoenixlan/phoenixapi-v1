from phoenixRest.models.core.event import Event
from phoenixRest.models.tickets.seatmap import Seatmap

import json
import transaction

from datetime import datetime, timedelta

def ensure_seatmap(testapp, token, event_uuid):
    event = testapp.get('/event/%s' % event_uuid, status=200).json_body
    if event['seatmap_uuid'] is not None:
        return
    
    seatmap = testapp.put_json('/seatmap', dict({
        'name': 'Test seatmap',
        'description': 'seatmap'
    }), headers=dict({
        "Authorization": "Bearer " + token
    }), status=200).json_body

    # Add a row
    row = testapp.put_json('/seatmap/%s/row' % seatmap['uuid'], dict({
        'row_number': 1,
        'x': 10,
        'y': 10,
        'horizontal': False
    }), headers=dict({
        "Authorization": "Bearer " + token
    }), status=200).json_body

    # Add three seats
    for i in range(0, 3):
        testapp.put_json('/row/%s/seat' % row['uuid'], dict({
        }), headers=dict({
            "Authorization": "Bearer " + token
        }), status=200).json_body

        
    # Re-fetch the seatmap
    seatmap = testapp.get('/seatmap/%s' % seatmap['uuid'], headers=dict({
        "Authorization": "Bearer " + token
    }), status=200).json_body

    # Set the seatmap as current for the event
    testapp.patch_json(f'/event/{event_uuid}', dict({
        'seatmap_uuid': seatmap['uuid']
    }), headers=dict({
        "Authorization": "Bearer " + token
    }), status=200).json_body


    return seatmap

def ensure_ticket(testapp, token, event_uuid):
    # Get existing ticket types
    res = testapp.get('/event/%s/ticketType' % event_uuid, headers=dict({
        "Authorization": "Bearer " + token
    }), status=200)
    ticket_type = res.json_body[0]

    current_user = testapp.get_user(token)

    # Give test a free ticket. Only works because test is an admin
    res = testapp.post_json('/ticket', dict({
        'ticket_type': ticket_type['uuid'],
        'recipient': current_user['uuid'],
        "event_uuid": str(event_uuid)
    }), headers=dict({
        "Authorization": "Bearer " + token
    }), status=200)

    # List the tickets owned by the test user
    owned_tickets = testapp.get('/user/%s/owned_tickets' % current_user['uuid'], headers=dict({
        "Authorization": "Bearer " + token
    }), status=200).json_body
    assert len(owned_tickets) > 0
    return owned_tickets[0]

def test_seatmap_wrong_event(testapp, db, upcoming_event, ticket_types):
    """Test that accessing seatmap availability with wrong event returns 400"""
    # test is an admin
    token, refresh = testapp.auth_get_tokens('test@example.com', 'sixcharacters')

    # Create a seatmap that is NOT associated with the event
    seatmap = testapp.put_json('/seatmap', dict({
        'name': 'Test seatmap',
        'description': 'seatmap'
    }), headers=dict({
        "Authorization": "Bearer " + token
    }), status=200).json_body

    # Try to get availability for an event that doesn't use this seatmap
    # This should return 400 because the event doesn't use this seatmap
    testapp.get('/seatmap/%s/availability?event_uuid=%s' % (seatmap['uuid'], upcoming_event.uuid), headers=dict({
        "Authorization": "Bearer " + token
    }), status=400)

def test_ticket_seating(testapp, db, upcoming_event, ticket_types):
    # test is an admin
    token, refresh = testapp.auth_get_tokens('test@example.com', 'sixcharacters')

    # Current event
    seatmap = ensure_seatmap(testapp, token, upcoming_event.uuid)

    seat_ticket = ensure_ticket(testapp, token, upcoming_event.uuid)

    availability = testapp.get('/seatmap/%s/availability?event_uuid=%s' % (seatmap['uuid'], upcoming_event.uuid), headers=dict({
        "Authorization": "Bearer " + token
    }), status=200).json_body

    seat = None
    for row in availability['rows']:
        for seat_candidate in row['seats']:
            if seat_candidate['taken'] == False:
                seat = seat_candidate
                print(json.dumps(seat))
                break
        else:
            continue
        break
        
    assert seat is not None

    # Make sure seating a ticket is illegal
    event_instance = db.query(Event).filter(Event.uuid == upcoming_event.uuid).first()
    event_instance.booking_time = datetime.now() 
    event_instance.seating_time_delta = 60*60
    transaction.commit()

    # Seat the ticket
    testapp.put_json('/ticket/%s/seat' % seat_ticket['ticket_id'], dict({
        'seat_uuid': seat['uuid']
    }), headers=dict({
        "Authorization": "Bearer " + token
    }), status=400)

    # Make sure sating is legal
    event_instance = db.query(Event).filter(Event.uuid == upcoming_event.uuid).first()
    event_instance.booking_time = datetime.now() - timedelta(days=1)
    event_instance.seating_time_delta = 30
    transaction.commit()

    # Seat again
    testapp.put_json('/ticket/%s/seat' % seat_ticket['ticket_id'], dict({
        'seat_uuid': seat['uuid']
    }), headers=dict({
        "Authorization": "Bearer " + token
    }), status=200)

    # Ensure the seatmap updated
    availability = testapp.get('/seatmap/%s/availability?event_uuid=%s' % (seatmap['uuid'], upcoming_event.uuid), headers=dict({
        "Authorization": "Bearer " + token
    }), status=200).json_body

    asserted = False
    for row in availability['rows']:
        for seat_candidate in row['seats']:
            if seat_candidate['uuid'] == seat['uuid']:
                assert seat_candidate['taken']
                asserted = True
        else:
            continue
        break
    assert asserted

    # Ensure the ticket now has a seat
    ticket = testapp.get('/ticket/%s' % seat_ticket['ticket_id'], headers=dict({
        "Authorization": "Bearer " + token
    }), status=200).json_body
    assert ticket['seat'] is not None
    assert ticket['seat']['uuid'] == seat['uuid']

def test_ticket_seating_non_current_event(testapp, db, event_brand, ticket_types):
    """Test that seating a ticket for a non-current event is rejected"""
    # test is an admin
    token, refresh = testapp.auth_get_tokens('test@example.com', 'sixcharacters')
    
    # Strategy: Create an even that is currently current. Set everything up. Then change its start and end time.
    earlier_event = Event("Earlier event", datetime.now() + timedelta(days=20), datetime.now() + timedelta(days=22), 400, event_brand)
    earlier_event.booking_time = datetime.now() + timedelta(days=2)
    earlier_event.seating_time_delta = 30
    db.add(earlier_event)
    db.flush()

    seatmap = ensure_seatmap(testapp, token, earlier_event.uuid)

    # Add ticket types to the earlier event
    all_ticket_types = testapp.get('/ticketType', headers=dict({
        'Authorization': "Bearer " + token
    }), status=200).json_body

    for ticket_type in all_ticket_types:
        testapp.put_json('/event/%s/ticketType' % earlier_event.uuid, dict({
            'ticket_type_uuid': ticket_type['uuid']
        }), headers=dict({
            'Authorization': "Bearer " + token
        }), status=200)

    # Create a ticket for the earlier event
    seat_ticket = ensure_ticket(testapp, token, earlier_event.uuid)

    # Get an available seat
    availability = testapp.get('/seatmap/%s/availability?event_uuid=%s' % (seatmap['uuid'], earlier_event.uuid), headers=dict({
        "Authorization": "Bearer " + token
    }), status=200).json_body

    seat = None
    for row in availability['rows']:
        for seat_candidate in row['seats']:
            if seat_candidate['taken'] == False:
                seat = seat_candidate
                break
        if seat:
            break

    assert seat is not None

    # Now move the event to be in the past, and test seating
    earlier_event.start_time = datetime.now() - timedelta(days=365)
    earlier_event.end_time = datetime.now() - timedelta(days=368)
    db.flush()

    # Try to seat the ticket - should fail because event is not current
    response = testapp.put_json('/ticket/%s/seat' % seat_ticket['ticket_id'], dict({
        'seat_uuid': seat['uuid']
    }), headers=dict({
        "Authorization": "Bearer " + token
    }), status=400).json_body

    assert 'error' in response
    assert 'not current' in response['error']

    # And create a new event in the future. Should still not work
    new_event = Event("Earlier event", datetime.now() + timedelta(days=300), datetime.now() + timedelta(days=303), 400, event_brand)
    new_event.booking_time = datetime.now() + timedelta(days=250)
    new_event.seating_time_delta = 30
    db.add(new_event)
    db.flush()
    
    response = testapp.put_json('/ticket/%s/seat' % seat_ticket['ticket_id'], dict({
        'seat_uuid': seat['uuid']
    }), headers=dict({
        "Authorization": "Bearer " + token
    }), status=400).json_body

    assert 'error' in response
    assert 'not current' in response['error']

def test_ticket_seating_wrong_seatmap(testapp, db, upcoming_event, ticket_types):
    """Test that seating a ticket on a seat from a different seatmap is rejected"""
    # test is an admin
    token, refresh = testapp.auth_get_tokens('test@example.com', 'sixcharacters')

    # Create seatmap for the event
    seatmap = ensure_seatmap(testapp, token, upcoming_event.uuid)
    seat_ticket = ensure_ticket(testapp, token, upcoming_event.uuid)

    # Create a DIFFERENT seatmap that is NOT associated with the event
    other_seatmap = testapp.put_json('/seatmap', dict({
        'name': 'Other seatmap',
        'description': 'different seatmap'
    }), headers=dict({
        "Authorization": "Bearer " + token
    }), status=200).json_body

    # Add a row to the other seatmap
    other_row = testapp.put_json('/seatmap/%s/row' % other_seatmap['uuid'], dict({
        'row_number': 1,
        'x': 10,
        'y': 10,
        'horizontal': False
    }), headers=dict({
        "Authorization": "Bearer " + token
    }), status=200).json_body

    # Add a seat to the other seatmap
    other_seat = testapp.put_json('/row/%s/seat' % other_row['uuid'], dict({
    }), headers=dict({
        "Authorization": "Bearer " + token
    }), status=200).json_body

    # Make sure seating is allowed time-wise
    event_instance = db.query(Event).filter(Event.uuid == upcoming_event.uuid).first()
    event_instance.booking_time = datetime.now() - timedelta(days=1)
    event_instance.seating_time_delta = 30
    transaction.commit()

    # Try to seat the ticket on a seat from the wrong seatmap - should fail
    response = testapp.put_json('/ticket/%s/seat' % seat_ticket['ticket_id'], dict({
        'seat_uuid': other_seat['uuid']
    }), headers=dict({
        "Authorization": "Bearer " + token
    }), status=400).json_body

    assert 'error' in response
    assert 'different seatmap' in response['error']