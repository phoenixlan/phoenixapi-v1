from phoenixRest.models.core.event import Event

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
        'recipient': current_user['uuid']
    }), headers=dict({
        "Authorization": "Bearer " + token
    }), status=200)

    # List the tickets owned by the test user
    owned_tickets = testapp.get('/user/%s/owned_tickets' % current_user['uuid'], headers=dict({
        "Authorization": "Bearer " + token 
    }), status=200).json_body
    assert len(owned_tickets) > 0
    return owned_tickets[0]

def test_ticket_seating(testapp, db):
    testapp.ensure_typical_event()
    # test is an admin
    token, refresh = testapp.auth_get_tokens('test', 'sixcharacters')

    # Current event
    current_event = testapp.get('/event/current', status=200).json_body
    assert current_event['uuid'] is not None
    seatmap = ensure_seatmap(testapp, token, current_event['uuid'])

    seat_ticket = ensure_ticket(testapp, token, current_event['uuid'])

    availability = testapp.get('/seatmap/%s/availability' % seatmap['uuid'], headers=dict({
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
    event_instance = db.query(Event).filter(Event.uuid == current_event['uuid']).first()
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
    event_instance = db.query(Event).filter(Event.uuid == current_event['uuid']).first()
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
    availability = testapp.get('/seatmap/%s/availability' % seatmap['uuid'], headers=dict({
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