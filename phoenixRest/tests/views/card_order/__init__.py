from test_app import TestApp

def test_card_order(testapp:TestApp):
    # Log in as an admin user
    admin_user_token, refresh = testapp.auth_get_tokens('test', 'sixcharacters')
    admin = testapp.get_user(admin_user_token)
    admin_uuid = admin["uuid"]
    
    #? ---- __init__.py ----
    # Admin orders a card for themself
    res = testapp.post_json('/card_order/', dict({
        "user_uuid" : admin_uuid
    }), headers=dict({
        'X-Phoenix-Auth': admin_user_token
    }), status=200)
    
    import uuid
    # Admin orders a card with the wrong user uuid
    res = testapp.post_json('/card_order/', dict({
        "user_uuid" : str(uuid.uuid4())
    }), headers=dict({
        'X-Phoenix-Auth': admin_user_token
    }), status=400)
    
    # Admin views all card orders i.e the one they created
    res = testapp.get('/card_order/', headers=dict({
        'X-Phoenix-Auth': admin_user_token
    }), status=200).json_body
    assert len(res) == 1
    
    #? ---- instance.py ----
    # We get the uuid of the created order
    card_order_uuid = res["uuid"]
    
    from phoenixRest.models.crew.card_order import OrderStates
    
    # Admin views the card order instance
    res = testapp.get(f'/card_order/{card_order_uuid}/', headers=dict({
        'X-Phoenix-Auth': admin_user_token
    }), status=200).json_body
    assert len(res) == 1
    assert res["state"] == OrderStates.CREATED.value
    
    # Admin orders the printing of the card
    res = testapp.patch(f'/card_order/{card_order_uuid}/generate', headers=dict({
        'X-Phoenix-Auth': admin_user_token
    }), status=200)
    assert res["state"] == OrderStates.IN_PROGRESS.value
    
    # Admin marks the order as finished
    res = testapp.patch(f'/card_order/{card_order_uuid}/finish', headers=dict({
        'X-Phoenix-Auth': admin_user_token
    }), status=200)
    assert res["state"] == OrderStates.FINISHED.value
    
    # Admin orders a new card for themself
    res = testapp.post_json('/card_order/', dict({
        "user_uuid" : admin_uuid
    }), headers=dict({
        'X-Phoenix-Auth': admin_user_token
    }), status=200)
    card_order_uuid = res["uuid"]
    
    # Admin marks the order as cancelled
    res = testapp.delete(f'/card_order/{card_order_uuid}/cancel', headers=dict({
        'X-Phoenix-Auth': admin_user_token
    }), status=200)
    assert res["state"] == OrderStates.CANCELLED.value
    
    # Admin orders the printing of the cancelled card
    res = testapp.patch(f'/card_order/{card_order_uuid}/generate', headers=dict({
        'X-Phoenix-Auth': admin_user_token
    }), status=403)