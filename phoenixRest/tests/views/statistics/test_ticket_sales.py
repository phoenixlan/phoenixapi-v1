from phoenixRest.models.core.event import Event

def test_smoketest_ticket_sales(db, testapp, ticketsale_ongoing_event):
    """Simple test that just makes sure ticket sales statistics isn't obviously broken
    """
    # test is an admin
    token, refresh = testapp.auth_get_tokens('test@example.com', 'sixcharacters')
    unprivileged_token, refresh = testapp.auth_get_tokens('jeff@example.com', 'sixcharacters')

    testapp.ensure_typical_event()

    stats = testapp.get('/statistics/ticket_sales', headers=dict({
        "Authorization": "Bearer " + token
    }), status=200).json_body

    all_events = db.query(Event).all()

    assert len(stats) == len(all_events)

    # No tickets should ever be sold
    current_stats = next(filter(lambda stat: stat["event"]["uuid"] == str(testapp.get_current_event(db).uuid), stats))
    assert sum(map(lambda day: day["count"], current_stats["days"])) == 0
    
    # Get ticket types for the next stage
    ticket_types = filter(
        lambda type: type["price"] > 0, 
        testapp.get(f'/event/{testapp.get_current_event(db).uuid}/ticketType', status=200).json_body
    )

    # Get unprivileged user UUID
    unprivileged_user = testapp.get_user(unprivileged_token)
    # Get a test user
    stats = testapp.get('/statistics/ticket_sales', headers=dict({
        "Authorization": "Bearer " + token
    }), status=200).json_body

    # Give test user two free tickets. Why two? To ensure no deduplication happens, etc.
    for i in range(0, 2):
        res = testapp.post_json('/ticket', dict({
            'ticket_type': next(ticket_types)['uuid'],
            'recipient': unprivileged_user['uuid']
        }), headers=dict({
            "Authorization": "Bearer " + token
        }), status=200)
        print(f"Ticket: {res.json_body}")

    # Ensure at least one ticket is sold
    stats = testapp.get('/statistics/ticket_sales', headers=dict({
        "Authorization": "Bearer " + token
    }), status=200).json_body

    current_event_uuid = str(testapp.get_current_event(db).uuid)
    print(f"Current event UUID: {current_event_uuid}")

    current_stats = next(filter(lambda stat: stat["event"]["uuid"] == current_event_uuid, stats))
    print(f"Stats: {current_stats}")

    # The two tickets should show up
    assert sum(map(lambda day: day["count"], current_stats["days"])) == 2