# Test if we can reserve a store session
def test_create_store_session(testapp):
    testapp.ensure_typical_event()
    res = testapp.get('/event/current', status=200)
    assert res.json_body['uuid'] is not None

    token, refresh = testapp.auth_get_tokens('test', 'sixcharacters')

    res = testapp.get('/event/%s/ticketType' % res.json_body['uuid'], headers=dict({
        "Authorization": "Bearer " + token
    }), status=200)

    # Reserve a card for the first ticket for sale, i guess
    res = testapp.put_json('/store_session', dict({
        'cart': [
            {'qty': 1, 'uuid': res.json_body[0]['uuid']}
        ]
    }), headers=dict({
        "Authorization": "Bearer " + token
    }), status=200)

    assert res.json_body['uuid'] is not None

