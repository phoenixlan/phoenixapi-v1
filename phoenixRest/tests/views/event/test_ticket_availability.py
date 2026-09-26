from phoenixRest.models.core.event_ticket_type_mapping import EventTicketTypeMapping
from phoenixRest.models.tickets.store_session import StoreSession

from datetime import datetime, timedelta


def _setup_event(testapp, admin_token, event, ticket_sales_caps, mappings):
    """Sets the sales caps of the event, and creates and maps a ticket type for each
    (name, grants_admission, sales_cap_groups, sales_cap) entry. Returns ticket type uuids by name"""
    headers = {'Authorization': "Bearer " + admin_token}
    testapp.patch_json('/event/%s' % event.uuid, {
        'ticket_sales_caps': ticket_sales_caps
    }, headers=headers, status=200)

    ticket_types = dict()
    for name, grants_admission, sales_cap_groups, sales_cap in mappings:
        ticket_type = testapp.post_json('/event_brand/%s/ticket_type' % event.event_brand_uuid, {
            'name': name,
            'price': 100,
            'refundable': True,
            'grants_admission': grants_admission,
            'seatable': grants_admission,
            'description': 'Ticket type used by ticket availability tests'
        }, headers=headers, status=200).json_body
        testapp.put_json('/event/%s/ticket_type_mapping' % event.uuid, {
            'ticket_type_uuid': ticket_type['uuid'],
            'sales_cap_groups': sales_cap_groups,
            'sales_cap': sales_cap
        }, headers=headers, status=200)
        ticket_types[name] = ticket_type['uuid']
    return ticket_types

def _sell(testapp, admin_token, event, ticket_type_uuid, recipient, amount):
    """Sells tickets by having an admin hand them out"""
    for i in range(0, amount):
        testapp.post_json('/event/%s/ticket' % event.uuid, {
            'ticket_type': ticket_type_uuid,
            'recipient': str(recipient.uuid)
        }, headers={'Authorization': "Bearer " + admin_token}, status=200)

def _availability(testapp, event):
    """Returns remaining tickets by ticket type uuid, and by group"""
    availability = testapp.get('/event/%s/ticket_availability' % event.uuid, status=200).json_body
    return (
        { entry['ticket_type']['uuid']: entry['remaining'] for entry in availability['ticket_types'] },
        { entry['group']: entry['remaining'] for entry in availability['groups'] }
    )

def _buy(testapp, token, event, cart, status):
    return testapp.put_json('/event/%s/store_session' % event.uuid, {
        'cart': [ {'uuid': uuid, 'qty': qty} for uuid, qty in cart.items() ]
    }, headers={'Authorization': "Bearer " + token}, status=status)


def test_other_group_sold_out(testapp, ticketsale_ongoing_event, admin_token, jeff_user, adam_user):
    """A ticket type can be bought when a ticket type in another group is sold out"""
    event = ticketsale_ongoing_event
    types = _setup_event(testapp, admin_token, event, {'floor': 1, 'balcony': 100}, [
        ('Floor', True, ['floor'], None),
        ('Balcony', True, ['balcony'], None),
    ])
    _sell(testapp, admin_token, event, types['Floor'], adam_user, 1)

    ticket_types, groups = _availability(testapp, event)
    assert ticket_types == {types['Floor']: 0, types['Balcony']: 100}
    assert groups == {'floor': 0, 'balcony': 100}

    token, refresh = testapp.auth_get_tokens(jeff_user.email, 'sixcharacters')
    _buy(testapp, token, event, {types['Floor']: 1}, 400)
    _buy(testapp, token, event, {types['Balcony']: 1}, 200)

def test_group_sold_out_type_has_plenty(testapp, ticketsale_ongoing_event, admin_token, jeff_user, adam_user):
    """A ticket type can't be bought when its group is sold out, even if the ticket type itself has plenty left"""
    event = ticketsale_ongoing_event
    types = _setup_event(testapp, admin_token, event, {'floor': 2}, [
        ('Floor', True, ['floor'], 10),
    ])
    _sell(testapp, admin_token, event, types['Floor'], adam_user, 2)

    ticket_types, groups = _availability(testapp, event)
    assert ticket_types == {types['Floor']: 0}
    assert groups == {'floor': 0}

    token, refresh = testapp.auth_get_tokens(jeff_user.email, 'sixcharacters')
    _buy(testapp, token, event, {types['Floor']: 1}, 400)

def test_type_sold_out_group_has_plenty(testapp, ticketsale_ongoing_event, admin_token, jeff_user, adam_user):
    """A ticket type can't be bought when it is sold out itself, even if its group has plenty left"""
    event = ticketsale_ongoing_event
    types = _setup_event(testapp, admin_token, event, {'floor': 100}, [
        ('Limited', True, ['floor'], 1),
        ('Unlimited', True, ['floor'], None),
    ])
    _sell(testapp, admin_token, event, types['Limited'], adam_user, 1)

    ticket_types, groups = _availability(testapp, event)
    assert ticket_types == {types['Limited']: 0, types['Unlimited']: 99}
    assert groups == {'floor': 99}

    token, refresh = testapp.auth_get_tokens(jeff_user.email, 'sixcharacters')
    _buy(testapp, token, event, {types['Limited']: 1}, 400)
    _buy(testapp, token, event, {types['Unlimited']: 1}, 200)

def test_shared_group_sold_out_other_groups_have_plenty(testapp, ticketsale_ongoing_event, admin_token, jeff_user, adam_user):
    """Ticket types that share a group can't be bought when it is sold out, even if their other groups have plenty left"""
    event = ticketsale_ongoing_event
    types = _setup_event(testapp, admin_token, event, {'total': 2, 'floor': 100, 'balcony': 100}, [
        ('Floor', True, ['floor', 'total'], None),
        ('Balcony', True, ['balcony', 'total'], None),
    ])
    _sell(testapp, admin_token, event, types['Floor'], adam_user, 2)

    ticket_types, groups = _availability(testapp, event)
    assert ticket_types == {types['Floor']: 0, types['Balcony']: 0}
    assert groups == {'total': 0, 'floor': 98, 'balcony': 100}

    token, refresh = testapp.auth_get_tokens(jeff_user.email, 'sixcharacters')
    _buy(testapp, token, event, {types['Floor']: 1}, 400)
    _buy(testapp, token, event, {types['Balcony']: 1}, 400)

def test_type_in_two_groups(testapp, ticketsale_ongoing_event, admin_token, jeff_user, adam_user):
    """A ticket type in two groups is limited by the minimum of both groups and its own cap"""
    event = ticketsale_ongoing_event
    types = _setup_event(testapp, admin_token, event, {'floor': 10, 'vip': 6}, [
        ('Floor VIP', True, ['floor', 'vip'], 4),
        ('Floor', True, ['floor'], None),
        ('VIP', True, ['vip'], None),
    ])
    token, refresh = testapp.auth_get_tokens(jeff_user.email, 'sixcharacters')

    # Its own cap is the limit
    ticket_types, groups = _availability(testapp, event)
    assert ticket_types[types['Floor VIP']] == 4
    _buy(testapp, token, event, {types['Floor VIP']: 5}, 400)

    # The vip group is the limit
    _sell(testapp, admin_token, event, types['VIP'], adam_user, 3)
    ticket_types, groups = _availability(testapp, event)
    assert groups == {'floor': 10, 'vip': 3}
    assert ticket_types[types['Floor VIP']] == 3
    _buy(testapp, token, event, {types['Floor VIP']: 4}, 400)

    # The floor group is the limit
    _sell(testapp, admin_token, event, types['Floor'], adam_user, 8)
    ticket_types, groups = _availability(testapp, event)
    assert groups == {'floor': 2, 'vip': 3}
    assert ticket_types[types['Floor VIP']] == 2
    _buy(testapp, token, event, {types['Floor VIP']: 3}, 400)

    # Selling the ticket type itself reduces every group it belongs to
    _sell(testapp, admin_token, event, types['Floor VIP'], adam_user, 1)
    ticket_types, groups = _availability(testapp, event)
    assert groups == {'floor': 1, 'vip': 2}
    assert ticket_types == {types['Floor VIP']: 1, types['Floor']: 1, types['VIP']: 2}
    _buy(testapp, token, event, {types['Floor VIP']: 2}, 400)
    _buy(testapp, token, event, {types['Floor VIP']: 1}, 200)

    ticket_types, groups = _availability(testapp, event)
    assert groups == {'floor': 0, 'vip': 1}
    assert ticket_types == {types['Floor VIP']: 0, types['Floor']: 0, types['VIP']: 1}

def test_combined_cart_exceeds_shared_group(testapp, ticketsale_ongoing_event, admin_token, jeff_user):
    """Ticket types that are available on their own can't be bought together if they exceed a group they share"""
    event = ticketsale_ongoing_event
    types = _setup_event(testapp, admin_token, event, {'floor': 3}, [
        ('A', True, ['floor'], None),
        ('B', True, ['floor'], None),
    ])
    token, refresh = testapp.auth_get_tokens(jeff_user.email, 'sixcharacters')

    _buy(testapp, token, event, {types['A']: 2, types['B']: 2}, 400)
    _buy(testapp, token, event, {types['A']: 2, types['B']: 1}, 200)

    ticket_types, groups = _availability(testapp, event)
    assert ticket_types == {types['A']: 0, types['B']: 0}
    assert groups == {'floor': 0}

def test_valid_store_sessions_are_counted(db, testapp, ticketsale_ongoing_event, admin_token, jeff_user, adam_user):
    """Tickets in store sessions that haven't expired are counted as sold"""
    event = ticketsale_ongoing_event
    types = _setup_event(testapp, admin_token, event, {'floor': 3}, [
        ('Floor', True, ['floor'], None),
    ])
    jeff_token, refresh = testapp.auth_get_tokens(jeff_user.email, 'sixcharacters')
    adam_token, refresh = testapp.auth_get_tokens(adam_user.email, 'sixcharacters')

    store_session = _buy(testapp, jeff_token, event, {types['Floor']: 2}, 200).json_body

    ticket_types, groups = _availability(testapp, event)
    assert ticket_types == {types['Floor']: 1}
    assert groups == {'floor': 1}
    _buy(testapp, adam_token, event, {types['Floor']: 2}, 400)

    # Once the store session expires, the tickets are available again
    db.query(StoreSession).filter(StoreSession.uuid == store_session['uuid']).one().expires = datetime.now() - timedelta(minutes=1)
    db.flush()

    ticket_types, groups = _availability(testapp, event)
    assert ticket_types == {types['Floor']: 3}
    assert groups == {'floor': 3}
    _buy(testapp, adam_token, event, {types['Floor']: 3}, 200)

def test_non_admission_ticket_types_count_towards_groups(testapp, ticketsale_ongoing_event, admin_token, jeff_user, adam_user):
    """Ticket types that don't grant admission count towards and are limited by their groups, like any other ticket type"""
    event = ticketsale_ongoing_event
    types = _setup_event(testapp, admin_token, event, {'floor': 2}, [
        ('Floor', True, ['floor'], None),
        ('Merch', False, ['floor'], 5),
    ])

    # Selling a non-admission ticket type reduces its group
    _sell(testapp, admin_token, event, types['Merch'], adam_user, 1)
    ticket_types, groups = _availability(testapp, event)
    assert groups == {'floor': 1}
    assert ticket_types == {types['Floor']: 1, types['Merch']: 1}

    # Non-admission ticket types are limited by their group, also when bought together with admission ticket types
    token, refresh = testapp.auth_get_tokens(jeff_user.email, 'sixcharacters')
    _buy(testapp, token, event, {types['Merch']: 2}, 400)
    _buy(testapp, token, event, {types['Floor']: 1, types['Merch']: 1}, 400)
    _buy(testapp, token, event, {types['Merch']: 1}, 200)

    # The non-admission purchase sold out the floor group for admission ticket types too
    ticket_types, groups = _availability(testapp, event)
    assert groups == {'floor': 0}
    assert ticket_types == {types['Floor']: 0, types['Merch']: 0}
    _buy(testapp, token, event, {types['Floor']: 1}, 400)

def test_non_admission_ticket_type_without_limits_is_unlimited(testapp, ticketsale_ongoing_event, admin_token, jeff_user, adam_user):
    """A non-admission ticket type without a sales cap or groups can be sold without limit"""
    event = ticketsale_ongoing_event
    types = _setup_event(testapp, admin_token, event, {'floor': 1}, [
        ('Floor', True, ['floor'], None),
        ('Merch', False, [], None),
    ])
    _sell(testapp, admin_token, event, types['Floor'], adam_user, 1)
    _sell(testapp, admin_token, event, types['Merch'], adam_user, 5)

    ticket_types, groups = _availability(testapp, event)
    assert ticket_types == {types['Floor']: 0, types['Merch']: None}
    assert groups == {'floor': 0}

    token, refresh = testapp.auth_get_tokens(jeff_user.email, 'sixcharacters')
    _buy(testapp, token, event, {types['Floor']: 1}, 400)
    _buy(testapp, token, event, {types['Merch']: 3}, 200)

    ticket_types, groups = _availability(testapp, event)
    assert ticket_types == {types['Floor']: 0, types['Merch']: None}

def test_availability_lists_groups_of_ticket_types(testapp, ticketsale_ongoing_event, admin_token):
    """Every ticket type belongs to exactly the groups it is mapped with, whether it grants admission or not"""
    event = ticketsale_ongoing_event
    types = _setup_event(testapp, admin_token, event, {'floor': 10}, [
        ('Floor', True, ['floor', 'balcony'], None),
        ('Merch', False, ['floor'], 5),
        ('Parking', False, [], None),
    ])

    availability = testapp.get('/event/%s/ticket_availability' % event.uuid, status=200).json_body
    groups = { entry['ticket_type']['uuid']: entry['groups'] for entry in availability['ticket_types'] }
    assert groups == {types['Floor']: ['floor', 'balcony'], types['Merch']: ['floor'], types['Parking']: []}

def test_all_is_not_a_special_group(testapp, ticketsale_ongoing_event, admin_token, jeff_user):
    """A group named all only limits the ticket types mapped to it, like any other group"""
    event = ticketsale_ongoing_event
    types = _setup_event(testapp, admin_token, event, {'all': 0, 'floor': 5}, [
        ('Floor', True, ['floor'], None),
        ('Everything', True, ['all'], None),
    ])

    ticket_types, groups = _availability(testapp, event)
    assert ticket_types == {types['Floor']: 5, types['Everything']: 0}
    assert groups == {'all': 0, 'floor': 5}

    token, refresh = testapp.auth_get_tokens(jeff_user.email, 'sixcharacters')
    _buy(testapp, token, event, {types['Everything']: 1}, 400)
    _buy(testapp, token, event, {types['Floor']: 1}, 200)

def test_misconfigured_ticket_type_is_not_sold(db, testapp, ticketsale_ongoing_event, admin_token, jeff_user):
    """An admission ticket type without a sales cap and groups can't be created through the API.
    If it exists anyway, selling it is refused"""
    event = ticketsale_ongoing_event
    types = _setup_event(testapp, admin_token, event, {}, [
        ('Floor', True, [], 5),
    ])
    mapping = db.query(EventTicketTypeMapping).filter(EventTicketTypeMapping.ticket_type_uuid == types['Floor']).one()
    mapping.sales_cap = None
    db.flush()

    token, refresh = testapp.auth_get_tokens(jeff_user.email, 'sixcharacters')
    res = _buy(testapp, token, event, {types['Floor']: 1}, 500)
    assert res.json_body['error'] == "Sorry! We configured it wrong"

def test_store_session_merges_duplicate_cart_entries(testapp, ticketsale_ongoing_event, admin_token, jeff_user):
    event = ticketsale_ongoing_event
    types = _setup_event(testapp, admin_token, event, {'floor': 3}, [
        ('Floor', True, ['floor'], None),
    ])
    token, refresh = testapp.auth_get_tokens(jeff_user.email, 'sixcharacters')

    store_session = testapp.put_json('/event/%s/store_session' % event.uuid, {
        'cart': [ {'uuid': types['Floor'], 'qty': 1}, {'uuid': types['Floor'], 'qty': 1} ]
    }, headers={'Authorization': "Bearer " + token}, status=200).json_body
    assert len(store_session['entries']) == 1
    assert store_session['entries'][0]['amount'] == 2

    # Merged entries are checked against availability together
    testapp.put_json('/event/%s/store_session' % event.uuid, {
        'cart': [ {'uuid': types['Floor'], 'qty': 1}, {'uuid': types['Floor'], 'qty': 1} ]
    }, headers={'Authorization': "Bearer " + token}, status=400)

def test_store_session_validation(testapp, ticketsale_ongoing_event, admin_token, jeff_user):
    event = ticketsale_ongoing_event
    types = _setup_event(testapp, admin_token, event, {'floor': 3}, [
        ('Floor', True, ['floor'], None),
    ])
    # A ticket type on the same brand that isn't mapped to the event
    unmapped = testapp.post_json('/event_brand/%s/ticket_type' % event.event_brand_uuid, {
        'name': 'Unmapped',
        'price': 100,
        'refundable': True,
        'grants_admission': True,
        'seatable': True,
        'description': 'Ticket type that is not mapped to the event'
    }, headers={'Authorization': "Bearer " + admin_token}, status=200).json_body

    token, refresh = testapp.auth_get_tokens(jeff_user.email, 'sixcharacters')
    headers = {'Authorization': "Bearer " + token}
    invalid_carts = [
        ([], "The cart is empty"),
        ([ {'uuid': types['Floor'], 'qty': 0} ], "The cart is empty"),
        ([ "not an object" ], "Cart entry is not an object"),
        ([ {'qty': 1} ], "Cart entry lacks uuid"),
        ([ {'uuid': types['Floor']} ], "Cart entry lacks qty"),
        ([ {'uuid': 1234, 'qty': 1} ], "Cart entry uuid is not a string"),
        ([ {'uuid': 'not-a-uuid', 'qty': 1} ], "Ticket type not found"),
        ([ {'uuid': types['Floor'], 'qty': "1"} ], "Quantity is not a number"),
        ([ {'uuid': types['Floor'], 'qty': True} ], "Quantity is not a number"),
        ([ {'uuid': types['Floor'], 'qty': -1} ], "Quantity is negative"),
        ([ {'uuid': unmapped['uuid'], 'qty': 1} ], "Ticket type is not available for this event"),
    ]
    for cart, error in invalid_carts:
        res = testapp.put_json('/event/%s/store_session' % event.uuid, {
            'cart': cart
        }, headers=headers, status=400)
        assert res.json_body['error'] == error

    testapp.put_json('/event/%s/store_session' % event.uuid, {
        'cart': "not a list"
    }, headers=headers, status=400)
