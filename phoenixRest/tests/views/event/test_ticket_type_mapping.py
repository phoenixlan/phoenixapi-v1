from phoenixRest.models.core.user import User
from phoenixRest.models.tickets.store_session import StoreSession

from datetime import datetime, timedelta

import uuid


def _create_ticket_type(testapp, admin_token, event, name, grants_admission=True):
    return testapp.post_json('/event_brand/%s/ticket_type' % event.event_brand_uuid, {
        'name': name,
        'price': 100,
        'refundable': True,
        'grants_admission': grants_admission,
        'seatable': grants_admission,
        'description': 'Ticket type used by ticket type mapping tests'
    }, headers={'Authorization': "Bearer " + admin_token}, status=200).json_body

def _ticket_type_names(testapp, event, token=None):
    headers = {'Authorization': "Bearer " + token} if token is not None else {}
    return sorted(ticket_type['name'] for ticket_type in testapp.get('/event/%s/ticketType' % event.uuid, headers=headers, status=200).json_body)


def test_mapping_permissions(testapp, upcoming_event, other_upcoming_event, admin_token, brand_admin_user, ticket_admin_user, jeff_user):
    """Admins, brand admins and ticket admins can create and list mappings. Nobody else can"""
    brand_admin_token, refresh = testapp.auth_get_tokens(brand_admin_user.email, 'sixcharacters')
    ticket_admin_token, refresh = testapp.auth_get_tokens(ticket_admin_user.email, 'sixcharacters')
    jeff_token, refresh = testapp.auth_get_tokens(jeff_user.email, 'sixcharacters')

    for i, token in enumerate([admin_token, brand_admin_token, ticket_admin_token]):
        ticket_type = _create_ticket_type(testapp, admin_token, upcoming_event, 'Ticket type %d' % i)
        mapping = testapp.put_json('/event/%s/ticket_type_mapping' % upcoming_event.uuid, {
            'ticket_type_uuid': ticket_type['uuid'],
            'sales_cap_groups': ['floor']
        }, headers={'Authorization': "Bearer " + token}, status=200).json_body
        assert mapping['ticket_type']['uuid'] == ticket_type['uuid']
        assert mapping['event_uuid'] == str(upcoming_event.uuid)
        assert mapping['sales_cap_groups'] == ['floor']
        assert mapping['sales_cap'] is None
        assert mapping['access_code'] is None

        mappings = testapp.get('/event/%s/ticket_type_mapping' % upcoming_event.uuid, headers={
            'Authorization': "Bearer " + token
        }, status=200).json_body
        assert len(mappings) == i + 1

    ticket_type = _create_ticket_type(testapp, admin_token, upcoming_event, 'Forbidden ticket type')
    for headers in [{'Authorization': "Bearer " + jeff_token}, {}]:
        testapp.put_json('/event/%s/ticket_type_mapping' % upcoming_event.uuid, {
            'ticket_type_uuid': ticket_type['uuid'],
            'sales_cap_groups': ['floor']
        }, headers=headers, status=403)
        testapp.get('/event/%s/ticket_type_mapping' % upcoming_event.uuid, headers=headers, status=403)

    # Ticket admins are scoped to their own brand
    testapp.get('/event/%s/ticket_type_mapping' % other_upcoming_event.uuid, headers={
        'Authorization': "Bearer " + ticket_admin_token
    }, status=403)
    testapp.put_json('/event/%s/ticket_type_mapping' % other_upcoming_event.uuid, {
        'ticket_type_uuid': ticket_type['uuid'],
        'sales_cap_groups': ['floor']
    }, headers={'Authorization': "Bearer " + ticket_admin_token}, status=403)

def test_admission_mapping_requires_sales_cap_or_group(testapp, upcoming_event, admin_token):
    """A mapping for a ticket type that grants admission and isn't limited by a sales cap or a group could admit an
    unlimited amount of people"""
    ticket_type = _create_ticket_type(testapp, admin_token, upcoming_event, 'Unlimited')
    headers = {'Authorization': "Bearer " + admin_token}

    res = testapp.put_json('/event/%s/ticket_type_mapping' % upcoming_event.uuid, {
        'ticket_type_uuid': ticket_type['uuid'],
        'sales_cap_groups': []
    }, headers=headers, status=400)
    assert res.json_body['error'] == "A ticket type mapping relating to a ticket type that grants admission must either have a sales_cap or belong to at least one sales cap group"

    res = testapp.put_json('/event/%s/ticket_type_mapping' % upcoming_event.uuid, {
        'ticket_type_uuid': ticket_type['uuid'],
        'sales_cap_groups': [],
        'sales_cap': None
    }, headers=headers, status=400)
    assert res.json_body['error'] == "A ticket type mapping relating to a ticket type that grants admission must either have a sales_cap or belong to at least one sales cap group"

    # Either a sales cap or a group is enough
    testapp.put_json('/event/%s/ticket_type_mapping' % upcoming_event.uuid, {
        'ticket_type_uuid': ticket_type['uuid'],
        'sales_cap_groups': [],
        'sales_cap': 0
    }, headers=headers, status=200)
    other_ticket_type = _create_ticket_type(testapp, admin_token, upcoming_event, 'Grouped')
    testapp.put_json('/event/%s/ticket_type_mapping' % upcoming_event.uuid, {
        'ticket_type_uuid': other_ticket_type['uuid'],
        'sales_cap_groups': ['floor']
    }, headers=headers, status=200)

def test_non_admission_mapping_may_be_unlimited(testapp, upcoming_event, admin_token):
    """A mapping for a ticket type that doesn't grant admission may have neither a sales cap nor a group"""
    ticket_type = _create_ticket_type(testapp, admin_token, upcoming_event, 'Merch', grants_admission=False)
    mapping = testapp.put_json('/event/%s/ticket_type_mapping' % upcoming_event.uuid, {
        'ticket_type_uuid': ticket_type['uuid'],
        'sales_cap_groups': []
    }, headers={'Authorization': "Bearer " + admin_token}, status=200).json_body
    assert mapping['sales_cap'] is None
    assert mapping['sales_cap_groups'] == []

def test_mapping_validation(testapp, upcoming_event, other_ticket_type, admin_token):
    ticket_type = _create_ticket_type(testapp, admin_token, upcoming_event, 'Validated')
    headers = {'Authorization': "Bearer " + admin_token}

    invalid_bodies = [
        ({'ticket_type_uuid': 'not-a-uuid', 'sales_cap_groups': ['floor']}, "Ticket type not found"),
        ({'ticket_type_uuid': str(uuid.uuid4()), 'sales_cap_groups': ['floor']}, "Ticket type not found"),
        ({'ticket_type_uuid': str(other_ticket_type.uuid), 'sales_cap_groups': ['floor']}, "Ticket type belongs to a different event brand"),
        ({'ticket_type_uuid': ticket_type['uuid'], 'sales_cap_groups': ['floor'], 'sales_cap': "5"}, "Invalid type of sales_cap (not integer or null)"),
        ({'ticket_type_uuid': ticket_type['uuid'], 'sales_cap_groups': ['floor'], 'sales_cap': True}, "Invalid type of sales_cap (not integer or null)"),
        ({'ticket_type_uuid': ticket_type['uuid'], 'sales_cap_groups': ['floor'], 'sales_cap': -1}, "sales_cap cannot be negative"),
        ({'ticket_type_uuid': ticket_type['uuid'], 'sales_cap_groups': [1]}, "Invalid type of sales_cap_groups entry (not string)"),
        ({'ticket_type_uuid': ticket_type['uuid'], 'sales_cap_groups': ['  '], 'sales_cap': 5}, "sales_cap_groups cannot contain an empty group name"),
        ({'ticket_type_uuid': ticket_type['uuid'], 'sales_cap_groups': ['floor', ' floor']}, "sales_cap_groups contains floor more than once"),
        ({'ticket_type_uuid': ticket_type['uuid'], 'sales_cap_groups': ['floor'], 'generate_code': "yes"}, "Invalid type of generate_code (not boolean)"),
    ]
    for body, error in invalid_bodies:
        res = testapp.put_json('/event/%s/ticket_type_mapping' % upcoming_event.uuid, body, headers=headers, status=400)
        assert res.json_body['error'] == error

    # Missing or wrongly typed required fields
    for body in [
        {'sales_cap_groups': ['floor']},
        {'ticket_type_uuid': ticket_type['uuid']},
        {'ticket_type_uuid': ticket_type['uuid'], 'sales_cap_groups': 'floor'},
        {'ticket_type_uuid': 1234, 'sales_cap_groups': ['floor']},
    ]:
        testapp.put_json('/event/%s/ticket_type_mapping' % upcoming_event.uuid, body, headers=headers, status=400)

    # Group names are stripped
    mapping = testapp.put_json('/event/%s/ticket_type_mapping' % upcoming_event.uuid, {
        'ticket_type_uuid': ticket_type['uuid'],
        'sales_cap_groups': [' floor ', 'vip'],
        'sales_cap': 5
    }, headers=headers, status=200).json_body
    assert mapping['sales_cap_groups'] == ['floor', 'vip']
    assert mapping['sales_cap'] == 5

    # A ticket type can only be mapped once per event
    res = testapp.put_json('/event/%s/ticket_type_mapping' % upcoming_event.uuid, {
        'ticket_type_uuid': ticket_type['uuid'],
        'sales_cap_groups': ['floor']
    }, headers=headers, status=400)
    assert res.json_body['error'] == "The ticket type is already mapped to this event"

def test_malformed_event_uuid(testapp):
    testapp.get('/event/not-a-uuid/ticketType', status=404)

def test_hidden_ticket_types(db, testapp, ticketsale_ongoing_event, admin_token, jeff_user, adam_user):
    """Ticket types with an access code are only visible and purchasable after unlocking them"""
    event = ticketsale_ongoing_event
    headers = {'Authorization': "Bearer " + admin_token}
    testapp.patch_json('/event/%s' % event.uuid, {'ticket_sales_caps': {'floor': 10}}, headers=headers, status=200)

    public = _create_ticket_type(testapp, admin_token, event, 'Public')
    testapp.put_json('/event/%s/ticket_type_mapping' % event.uuid, {
        'ticket_type_uuid': public['uuid'],
        'sales_cap_groups': ['floor']
    }, headers=headers, status=200)
    hidden = _create_ticket_type(testapp, admin_token, event, 'Hidden')
    hidden_mapping = testapp.put_json('/event/%s/ticket_type_mapping' % event.uuid, {
        'ticket_type_uuid': hidden['uuid'],
        'sales_cap_groups': ['floor'],
        'generate_code': True
    }, headers=headers, status=200).json_body
    access_code = hidden_mapping['access_code']
    assert access_code is not None
    assert len(access_code) == 10

    # Admins see the access code when listing mappings
    mappings = testapp.get('/event/%s/ticket_type_mapping' % event.uuid, headers=headers, status=200).json_body
    assert { mapping['ticket_type']['uuid']: mapping['access_code'] for mapping in mappings } == {
        public['uuid']: None,
        hidden['uuid']: access_code
    }

    jeff_token, refresh = testapp.auth_get_tokens(jeff_user.email, 'sixcharacters')
    adam_token, refresh = testapp.auth_get_tokens(adam_user.email, 'sixcharacters')

    assert _ticket_type_names(testapp, event) == ['Public']
    assert _ticket_type_names(testapp, event, jeff_token) == ['Public']

    availability = testapp.get('/event/%s/ticket_availability' % event.uuid, headers={
        'Authorization': "Bearer " + jeff_token
    }, status=200).json_body
    assert [ entry['ticket_type']['uuid'] for entry in availability['ticket_types'] ] == [public['uuid']]

    res = testapp.put_json('/event/%s/store_session' % event.uuid, {
        'cart': [{'uuid': hidden['uuid'], 'qty': 1}]
    }, headers={'Authorization': "Bearer " + jeff_token}, status=400)
    assert res.json_body['error'] == "Ticket type is not available for this event"

    # Unlocking validation
    testapp.post_json('/event/%s/unlock_ticket_type' % event.uuid, {'code': access_code}, status=403)
    for body in [{}, {'code': 1234}, {'code': ''}, {'code': '   '}]:
        testapp.post_json('/event/%s/unlock_ticket_type' % event.uuid, body, headers={
            'Authorization': "Bearer " + jeff_token
        }, status=400)

    res = testapp.post_json('/event/%s/unlock_ticket_type' % event.uuid, {'code': 'wrongcode'}, headers={
        'Authorization': "Bearer " + jeff_token
    }, status=200).json_body
    assert res == {'success': False}
    assert _ticket_type_names(testapp, event, jeff_token) == ['Public']

    res = testapp.post_json('/event/%s/unlock_ticket_type' % event.uuid, {'code': access_code}, headers={
        'Authorization': "Bearer " + jeff_token
    }, status=200).json_body
    assert res == {'success': True}

    # Jeff can now see and buy the hidden ticket type
    assert _ticket_type_names(testapp, event, jeff_token) == ['Hidden', 'Public']
    availability = testapp.get('/event/%s/ticket_availability' % event.uuid, headers={
        'Authorization': "Bearer " + jeff_token
    }, status=200).json_body
    assert sorted(entry['ticket_type']['uuid'] for entry in availability['ticket_types']) == sorted([public['uuid'], hidden['uuid']])
    testapp.put_json('/event/%s/store_session' % event.uuid, {
        'cart': [{'uuid': hidden['uuid'], 'qty': 1}]
    }, headers={'Authorization': "Bearer " + jeff_token}, status=200)

    # Nobody else can
    assert _ticket_type_names(testapp, event) == ['Public']
    assert _ticket_type_names(testapp, event, adam_token) == ['Public']

    # Unlocking again succeeds without activating the ticket type twice
    res = testapp.post_json('/event/%s/unlock_ticket_type' % event.uuid, {'code': access_code}, headers={
        'Authorization': "Bearer " + jeff_token
    }, status=200).json_body
    assert res == {'success': True}
    jeff = db.query(User).filter(User.uuid == jeff_user.uuid).one()
    assert len(jeff.event_ticket_type_activations) == 1

def test_delete_mapping_permissions(db, testapp, upcoming_event, other_upcoming_event, other_ticket_type, admin_token, brand_admin_user, ticket_admin_user, jeff_user):
    """Admins, brand admins and ticket admins can delete mappings. Nobody else can"""
    brand_admin_token, refresh = testapp.auth_get_tokens(brand_admin_user.email, 'sixcharacters')
    ticket_admin_token, refresh = testapp.auth_get_tokens(ticket_admin_user.email, 'sixcharacters')
    jeff_token, refresh = testapp.auth_get_tokens(jeff_user.email, 'sixcharacters')
    admin_headers = {'Authorization': "Bearer " + admin_token}

    for i, token in enumerate([admin_token, brand_admin_token, ticket_admin_token]):
        ticket_type = _create_ticket_type(testapp, admin_token, upcoming_event, 'Ticket type %d' % i)
        mapping = testapp.put_json('/event/%s/ticket_type_mapping' % upcoming_event.uuid, {
            'ticket_type_uuid': ticket_type['uuid'],
            'sales_cap_groups': ['floor']
        }, headers=admin_headers, status=200).json_body

        # Nobody without permissions can delete it
        testapp.delete('/event_ticket_type_mapping/%s' % mapping['uuid'], headers={
            'Authorization': "Bearer " + jeff_token
        }, status=403)
        testapp.delete('/event_ticket_type_mapping/%s' % mapping['uuid'], status=403)

        res = testapp.delete('/event_ticket_type_mapping/%s' % mapping['uuid'], headers={
            'Authorization': "Bearer " + token
        }, status=200).json_body
        assert res == {'success': True}
        # The session is shared with the test. Flush the deletion, and expire relationships loaded before it
        db.flush()
        db.expire_all()

        mappings = testapp.get('/event/%s/ticket_type_mapping' % upcoming_event.uuid, headers=admin_headers, status=200).json_body
        assert len(mappings) == 0
        assert _ticket_type_names(testapp, upcoming_event) == []

    # A deleted ticket type can be mapped again
    testapp.put_json('/event/%s/ticket_type_mapping' % upcoming_event.uuid, {
        'ticket_type_uuid': ticket_type['uuid'],
        'sales_cap_groups': ['floor']
    }, headers=admin_headers, status=200)

    # Ticket admins are scoped to their own brand
    other_mapping = testapp.put_json('/event/%s/ticket_type_mapping' % other_upcoming_event.uuid, {
        'ticket_type_uuid': str(other_ticket_type.uuid),
        'sales_cap_groups': ['floor']
    }, headers=admin_headers, status=200).json_body
    testapp.delete('/event_ticket_type_mapping/%s' % other_mapping['uuid'], headers={
        'Authorization': "Bearer " + ticket_admin_token
    }, status=403)
    testapp.delete('/event_ticket_type_mapping/%s' % other_mapping['uuid'], headers={
        'Authorization': "Bearer " + brand_admin_token
    }, status=403)

def test_delete_mapping_not_found(testapp, admin_token):
    headers = {'Authorization': "Bearer " + admin_token}
    testapp.delete('/event_ticket_type_mapping/not-a-uuid', headers=headers, status=404)
    testapp.delete('/event_ticket_type_mapping/%s' % uuid.uuid4(), headers=headers, status=404)

def test_delete_unlocked_mapping(db, testapp, ticketsale_ongoing_event, admin_token, jeff_user):
    """Deleting a mapping also removes it from the users who have unlocked it"""
    event = ticketsale_ongoing_event
    headers = {'Authorization': "Bearer " + admin_token}
    hidden = _create_ticket_type(testapp, admin_token, event, 'Hidden')
    mapping = testapp.put_json('/event/%s/ticket_type_mapping' % event.uuid, {
        'ticket_type_uuid': hidden['uuid'],
        'sales_cap_groups': ['floor'],
        'generate_code': True
    }, headers=headers, status=200).json_body

    jeff_token, refresh = testapp.auth_get_tokens(jeff_user.email, 'sixcharacters')
    testapp.post_json('/event/%s/unlock_ticket_type' % event.uuid, {'code': mapping['access_code']}, headers={
        'Authorization': "Bearer " + jeff_token
    }, status=200)
    assert _ticket_type_names(testapp, event, jeff_token) == ['Hidden']

    testapp.delete('/event_ticket_type_mapping/%s' % mapping['uuid'], headers=headers, status=200)
    db.flush()
    db.expire_all()

    assert _ticket_type_names(testapp, event, jeff_token) == []
    jeff = db.query(User).filter(User.uuid == jeff_user.uuid).one()
    assert len(jeff.event_ticket_type_activations) == 0

    # The old code no longer unlocks anything
    res = testapp.post_json('/event/%s/unlock_ticket_type' % event.uuid, {'code': mapping['access_code']}, headers={
        'Authorization': "Bearer " + jeff_token
    }, status=200).json_body
    assert res == {'success': False}

def test_delete_mapping_with_sales(db, testapp, ticketsale_ongoing_event, admin_token, jeff_user):
    """A mapping can't be deleted while tickets of its type are sold or reserved, as that would free up their spots"""
    event = ticketsale_ongoing_event
    headers = {'Authorization': "Bearer " + admin_token}
    sold = _create_ticket_type(testapp, admin_token, event, 'Sold')
    sold_mapping = testapp.put_json('/event/%s/ticket_type_mapping' % event.uuid, {
        'ticket_type_uuid': sold['uuid'],
        'sales_cap_groups': ['floor']
    }, headers=headers, status=200).json_body
    reserved = _create_ticket_type(testapp, admin_token, event, 'Reserved')
    reserved_mapping = testapp.put_json('/event/%s/ticket_type_mapping' % event.uuid, {
        'ticket_type_uuid': reserved['uuid'],
        'sales_cap_groups': ['floor']
    }, headers=headers, status=200).json_body

    testapp.post_json('/event/%s/ticket' % event.uuid, {
        'ticket_type': sold['uuid'],
        'recipient': str(jeff_user.uuid)
    }, headers=headers, status=200)
    res = testapp.delete('/event_ticket_type_mapping/%s' % sold_mapping['uuid'], headers=headers, status=400).json_body
    assert res['error'] == "Tickets of this type have already been sold for the event"

    jeff_token, refresh = testapp.auth_get_tokens(jeff_user.email, 'sixcharacters')
    store_session = testapp.put_json('/event/%s/store_session' % event.uuid, {
        'cart': [{'uuid': reserved['uuid'], 'qty': 1}]
    }, headers={'Authorization': "Bearer " + jeff_token}, status=200).json_body
    res = testapp.delete('/event_ticket_type_mapping/%s' % reserved_mapping['uuid'], headers=headers, status=400).json_body
    assert res['error'] == "Tickets of this type are currently reserved by someone buying them"

    # Once the store session expires, the mapping can be deleted
    db.query(StoreSession).filter(StoreSession.uuid == store_session['uuid']).one().expires = datetime.now() - timedelta(minutes=1)
    db.flush()
    testapp.delete('/event_ticket_type_mapping/%s' % reserved_mapping['uuid'], headers=headers, status=200)
    db.flush()
    db.expire_all()

    mappings = testapp.get('/event/%s/ticket_type_mapping' % event.uuid, headers=headers, status=200).json_body
    assert [ mapping['uuid'] for mapping in mappings ] == [sold_mapping['uuid']]

def test_rotate_access_code_permissions(testapp, upcoming_event, other_upcoming_event, other_ticket_type, admin_token, brand_admin_user, ticket_admin_user, jeff_user):
    """Admins, brand admins and ticket admins can rotate access codes. Nobody else can"""
    brand_admin_token, refresh = testapp.auth_get_tokens(brand_admin_user.email, 'sixcharacters')
    ticket_admin_token, refresh = testapp.auth_get_tokens(ticket_admin_user.email, 'sixcharacters')
    jeff_token, refresh = testapp.auth_get_tokens(jeff_user.email, 'sixcharacters')
    admin_headers = {'Authorization': "Bearer " + admin_token}

    hidden = _create_ticket_type(testapp, admin_token, upcoming_event, 'Hidden')
    mapping = testapp.put_json('/event/%s/ticket_type_mapping' % upcoming_event.uuid, {
        'ticket_type_uuid': hidden['uuid'],
        'sales_cap_groups': ['floor'],
        'generate_code': True
    }, headers=admin_headers, status=200).json_body

    testapp.post('/event_ticket_type_mapping/%s/rotate' % mapping['uuid'], headers={
        'Authorization': "Bearer " + jeff_token
    }, status=403)
    testapp.post('/event_ticket_type_mapping/%s/rotate' % mapping['uuid'], status=403)

    access_code = mapping['access_code']
    for token in [admin_token, brand_admin_token, ticket_admin_token]:
        rotated = testapp.post('/event_ticket_type_mapping/%s/rotate' % mapping['uuid'], headers={
            'Authorization': "Bearer " + token
        }, status=200).json_body
        assert rotated['uuid'] == mapping['uuid']
        assert rotated['access_code'] != access_code
        assert len(rotated['access_code']) == 10
        access_code = rotated['access_code']

    # Brand and ticket admins are scoped to their own brand
    other_mapping = testapp.put_json('/event/%s/ticket_type_mapping' % other_upcoming_event.uuid, {
        'ticket_type_uuid': str(other_ticket_type.uuid),
        'sales_cap_groups': ['floor'],
        'generate_code': True
    }, headers=admin_headers, status=200).json_body
    for token in [brand_admin_token, ticket_admin_token]:
        testapp.post('/event_ticket_type_mapping/%s/rotate' % other_mapping['uuid'], headers={
            'Authorization': "Bearer " + token
        }, status=403)

def test_rotate_requires_access_code(testapp, upcoming_event, admin_token):
    headers = {'Authorization': "Bearer " + admin_token}
    public = _create_ticket_type(testapp, admin_token, upcoming_event, 'Public')
    mapping = testapp.put_json('/event/%s/ticket_type_mapping' % upcoming_event.uuid, {
        'ticket_type_uuid': public['uuid'],
        'sales_cap_groups': ['floor']
    }, headers=headers, status=200).json_body

    res = testapp.post('/event_ticket_type_mapping/%s/rotate' % mapping['uuid'], headers=headers, status=400).json_body
    assert res['error'] == "The ticket type mapping has no access code to rotate"

    mappings = testapp.get('/event/%s/ticket_type_mapping' % upcoming_event.uuid, headers=headers, status=200).json_body
    assert mappings[0]['access_code'] is None

def test_rotate_not_found(testapp, admin_token):
    headers = {'Authorization': "Bearer " + admin_token}
    testapp.post('/event_ticket_type_mapping/not-a-uuid/rotate', headers=headers, status=404)
    testapp.post('/event_ticket_type_mapping/%s/rotate' % uuid.uuid4(), headers=headers, status=404)

def test_rotate_access_code(testapp, ticketsale_ongoing_event, admin_token, jeff_user, adam_user):
    """After rotating, only the new code unlocks the ticket type. Users who unlocked it with the old code keep access"""
    event = ticketsale_ongoing_event
    headers = {'Authorization': "Bearer " + admin_token}
    hidden = _create_ticket_type(testapp, admin_token, event, 'Hidden')
    mapping = testapp.put_json('/event/%s/ticket_type_mapping' % event.uuid, {
        'ticket_type_uuid': hidden['uuid'],
        'sales_cap_groups': ['floor'],
        'generate_code': True
    }, headers=headers, status=200).json_body
    old_code = mapping['access_code']

    jeff_token, refresh = testapp.auth_get_tokens(jeff_user.email, 'sixcharacters')
    adam_token, refresh = testapp.auth_get_tokens(adam_user.email, 'sixcharacters')
    testapp.post_json('/event/%s/unlock_ticket_type' % event.uuid, {'code': old_code}, headers={
        'Authorization': "Bearer " + jeff_token
    }, status=200)

    new_code = testapp.post('/event_ticket_type_mapping/%s/rotate' % mapping['uuid'], headers=headers, status=200).json_body['access_code']
    assert new_code != old_code

    mappings = testapp.get('/event/%s/ticket_type_mapping' % event.uuid, headers=headers, status=200).json_body
    assert mappings[0]['access_code'] == new_code

    # Jeff unlocked it before the rotation and keeps access
    assert _ticket_type_names(testapp, event, jeff_token) == ['Hidden']

    # The old code no longer unlocks anything
    res = testapp.post_json('/event/%s/unlock_ticket_type' % event.uuid, {'code': old_code}, headers={
        'Authorization': "Bearer " + adam_token
    }, status=200).json_body
    assert res == {'success': False}
    assert _ticket_type_names(testapp, event, adam_token) == []

    res = testapp.post_json('/event/%s/unlock_ticket_type' % event.uuid, {'code': new_code}, headers={
        'Authorization': "Bearer " + adam_token
    }, status=200).json_body
    assert res == {'success': True}
    assert _ticket_type_names(testapp, event, adam_token) == ['Hidden']

def test_access_code_is_scoped_to_event(testapp, ticketsale_ongoing_event, upcoming_event, admin_token, jeff_user):
    """An access code only unlocks ticket types on the event it belongs to"""
    headers = {'Authorization': "Bearer " + admin_token}
    hidden = _create_ticket_type(testapp, admin_token, ticketsale_ongoing_event, 'Hidden')
    access_code = testapp.put_json('/event/%s/ticket_type_mapping' % ticketsale_ongoing_event.uuid, {
        'ticket_type_uuid': hidden['uuid'],
        'sales_cap_groups': ['floor'],
        'generate_code': True
    }, headers=headers, status=200).json_body['access_code']

    jeff_token, refresh = testapp.auth_get_tokens(jeff_user.email, 'sixcharacters')
    res = testapp.post_json('/event/%s/unlock_ticket_type' % upcoming_event.uuid, {'code': access_code}, headers={
        'Authorization': "Bearer " + jeff_token
    }, status=200).json_body
    assert res == {'success': False}
