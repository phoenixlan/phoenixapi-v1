# Test if we can reserve a store session
def test_create_store_session(testapp, upcoming_event, ticket_types, admin_user):
    token, refresh = testapp.auth_get_tokens(admin_user.email, 'sixcharacters')

    res = testapp.get('/event/%s/ticketType' % upcoming_event.uuid, headers=dict({
        "Authorization": "Bearer " + token
    }), status=200)

    # Reserve a card for the first ticket for sale, i guess
    res = testapp.put_json('/event/%s/store_session' % upcoming_event.uuid, dict({
        'cart': [
            {'qty': 1, 'uuid': res.json_body[0]['uuid']}
        ]
    }), headers=dict({
        "Authorization": "Bearer " + token
    }), status=200)

    assert res.json_body['uuid'] is not None

def test_store_session_rejects_ticket_type_from_other_brand(
        testapp, upcoming_event, other_ticket_type, admin_token):
    response = testapp.put_json(
        '/event/%s/store_session' % upcoming_event.uuid,
        {
            'cart': [{'qty': 1, 'uuid': str(other_ticket_type.uuid)}]
        },
        headers={'Authorization': "Bearer " + admin_token},
        status=400
    )

    assert response.json_body['error'] == \
        'Ticket type belongs to a different event brand'
