from phoenixRest.models.core.event import Event
from phoenixRest.models.core.user import User
from phoenixRest.models.crew.position_mapping import PositionMapping
from phoenixRest.models.crew.position import Position
from phoenixRest.models.tickets.ticket import Ticket
from phoenixRest.models.tickets.ticket_type import TicketType

import pytest 
import logging
log = logging.getLogger(__name__)

@pytest.mark.skip(reason="Known broken")
def test_participant_history_smoketest(db, testapp):
    """Test participant history using seeded data
    """
    # test is an admin
    token, refresh = testapp.auth_get_tokens('test@example.com', 'sixcharacters')
    unprivileged_token, refresh = testapp.auth_get_tokens('jeff@example.com', 'sixcharacters')
    unprivileged_user = testapp.get_user(unprivileged_token)

    unprivileged_token_two, _ = testapp.auth_get_tokens('adam@example.com', 'sixcharacters')
    unprivileged_user_two = testapp.get_user(unprivileged_token_two)

    testapp.ensure_typical_event()

    stats = testapp.get('/statistics/participant_history', headers=dict({
        "Authorization": "Bearer " + token
    }), status=200).json_body

    all_events = db.query(Event).all()
    # reverse gives descending sort
    all_sorted_events = sorted(all_events, key=lambda event: event.start_time.timestamp(), reverse=True)
    assert len(all_sorted_events) > 0

    # Ensure it produced stats for all events.
    assert len(stats) == len(all_events)

    # The next part is tricky and depends on the pre-seeded data
    def test_event(event_uuid, counts, crew_counts):
        event_stats = next(filter(lambda stat_obj: stat_obj["event"]["uuid"] == event_uuid, stats))

        assert event_stats["counts"] == counts
        assert event_stats["crew_counts"] == crew_counts
    
    # No guests
    for event in all_sorted_events:
        test_event(str(event.uuid), [], [])

    # Create a free ticket for current event - what happens?
    ticket_types = filter(
        lambda type: type["price"] > 0, 
        testapp.get(f'/event/{testapp.get_current_event(db).uuid}/ticketType', status=200).json_body
    )
    paid_ticket_type = next(ticket_types)

    res = testapp.post_json('/ticket', dict({
        'ticket_type': paid_ticket_type['uuid'],
        'recipient': unprivileged_user['uuid']
    }), headers=dict({
        "Authorization": "Bearer " + token
    }), status=200)

    # Refresh the stats
    stats = testapp.get('/statistics/participant_history', headers=dict({
        "Authorization": "Bearer " + token
    }), status=200).json_body

    # The person we gave a ticket has no experience
    test_event(str(all_sorted_events[0].uuid), [1], [])
    test_event(str(all_sorted_events[1].uuid), [], [])
    test_event(str(all_sorted_events[2].uuid), [], [])
    test_event(str(all_sorted_events[3].uuid), [], [])
    test_event(str(all_sorted_events[4].uuid), [], [])
    test_event(str(all_sorted_events[5].uuid), [], [])

    # Give the same person another ticket, it should not change anything
    res = testapp.post_json('/ticket', dict({
        'ticket_type': paid_ticket_type['uuid'],
        'recipient': unprivileged_user['uuid']
    }), headers=dict({
        "Authorization": "Bearer " + token
    }), status=200)

    # Refresh the stats
    stats = testapp.get('/statistics/participant_history', headers=dict({
        "Authorization": "Bearer " + token
    }), status=200).json_body

    test_event(str(all_sorted_events[0].uuid), [1], [])
    test_event(str(all_sorted_events[1].uuid), [], [])
    test_event(str(all_sorted_events[2].uuid), [], [])
    test_event(str(all_sorted_events[3].uuid), [], [])
    test_event(str(all_sorted_events[4].uuid), [], [])
    test_event(str(all_sorted_events[5].uuid), [], [])

    # Now give the person a ticket for the previous event. They should correctly show up as having experience
    ticket_user = db.query(User).filter(User.uuid == unprivileged_user['uuid']).first()
    ticket_type = db.query(TicketType).filter(TicketType.uuid == paid_ticket_type['uuid']).first()
    t = Ticket(ticket_user, None, ticket_type, all_sorted_events[1])
    db.add(t)

    # Refresh the stats
    stats = testapp.get('/statistics/participant_history', headers=dict({
        "Authorization": "Bearer " + token
    }), status=200).json_body

    all_tickets = db.query(Ticket).all()

    test_event(str(all_sorted_events[0].uuid), [0, 1], [])
    test_event(str(all_sorted_events[1].uuid), [1], [])
    test_event(str(all_sorted_events[2].uuid), [], [])
    test_event(str(all_sorted_events[3].uuid), [], [])
    test_event(str(all_sorted_events[4].uuid), [], [])
    test_event(str(all_sorted_events[5].uuid), [], [])

    # Last, give a ticket to another user and see what happens
    res = testapp.post_json('/ticket', dict({
        'ticket_type': paid_ticket_type['uuid'],
        'recipient': unprivileged_user_two['uuid']
    }), headers=dict({
        "Authorization": "Bearer " + token
    }), status=200)

    # Refresh the stats
    stats = testapp.get('/statistics/participant_history', headers=dict({
        "Authorization": "Bearer " + token
    }), status=200).json_body

    test_event(str(all_sorted_events[0].uuid), [1, 1], [])
    test_event(str(all_sorted_events[1].uuid), [1], [])
    test_event(str(all_sorted_events[2].uuid), [], [])
    test_event(str(all_sorted_events[3].uuid), [], [])
    test_event(str(all_sorted_events[4].uuid), [], [])
    test_event(str(all_sorted_events[5].uuid), [], [])

@pytest.mark.skip(reason="Known broken")
def test_participant_history_crew(db, testapp):
    """Test participant history, but this time we add some crew memberships to be tested
    """
    # test is an admin
    token, refresh = testapp.auth_get_tokens('test@example.com', 'sixcharacters')
    unprivileged_token, refresh = testapp.auth_get_tokens('jeff@example.com', 'sixcharacters')
    unprivileged_user = testapp.get_user(unprivileged_token)

    stats = testapp.get('/statistics/participant_history', headers=dict({
        "Authorization": "Bearer " + token
    }), status=200).json_body

    all_events = db.query(Event).all()
    # reverse gives descending sort
    all_sorted_events = sorted(all_events, key=lambda event: event.start_time.timestamp(), reverse=True)
    assert len(all_sorted_events) > 0

    # Ensure it produced stats for all events.
    assert len(stats) == len(all_events)

    def test_event(event_uuid, counts, crew_counts):
        event_stats = next(filter(lambda stat_obj: stat_obj["event"]["uuid"] == event_uuid, stats))

        assert event_stats["counts"] == counts
        assert event_stats["crew_counts"] == crew_counts

    # No people with experience what so ever
    test_event(str(all_sorted_events[0].uuid), [], [])

    # Now add someone to a crew
    # Pick a position that actually belongs to a crew
    position_candidates = list(filter(lambda f: f["crew_uuid"] is not None, testapp.get('/position', headers=dict({
        "Authorization": "Bearer " + token
    }), status=200).json_body))

    created_mapping = testapp.post_json('/position_mapping', {
        "position_uuid": position_candidates[0]['uuid'],
        "user_uuid": unprivileged_user['uuid']
    }, headers=dict({
        "Authorization": "Bearer " + token
    }), status=200).json_body

    # Refresh
    stats = testapp.get('/statistics/participant_history', headers=dict({
        "Authorization": "Bearer " + token
    }), status=200).json_body

    # There should be a crew member with 0 experience!
    test_event(str(all_sorted_events[0].uuid), [], [1])

    # Now try to create a position mapping for last event.
    position_user = db.query(User).filter(User.uuid == unprivileged_user['uuid']).first()
    position = db.query(Position).filter(Position.uuid == position_candidates[0]['uuid']).first()
    assert position is not None
    last_mapping = PositionMapping(position_user, position, all_sorted_events[1])
    db.add(last_mapping)

    # Refresh
    stats = testapp.get('/statistics/participant_history', headers=dict({
        "Authorization": "Bearer " + token
    }), status=200).json_body

    # There should be a crew member with 1 year of experience!
    test_event(str(all_sorted_events[0].uuid), [], [0, 1])

    # Add them to another crew, shouldnt change the output
    created_mapping = testapp.post_json('/position_mapping', {
        "position_uuid": position_candidates[1]['uuid'],
        "user_uuid": unprivileged_user['uuid']
    }, headers=dict({
        "Authorization": "Bearer " + token
    }), status=200).json_body

    stats = testapp.get('/statistics/participant_history', headers=dict({
        "Authorization": "Bearer " + token
    }), status=200).json_body

    test_event(str(all_sorted_events[0].uuid), [], [0, 1])