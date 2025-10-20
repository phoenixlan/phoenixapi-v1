from test_app import TestApp
import uuid
from phoenixRest.models.crew.card_order import OrderStates

def test_card_order(testapp:TestApp, upcoming_event):
    # Log in as an admin user
    admin_user_token, refresh = testapp.auth_get_tokens("test@example.com", "sixcharacters")
    admin = testapp.get_user(admin_user_token)
    admin_uuid = admin["uuid"]
    
    # We ensure that admin has an avatar
    testapp.upload_avatar(admin_user_token, "phoenixRest/tests/assets/avatar_test.png", 10, 10, 600, 450, expected_status=200)
    
    #? ---- __init__.py ----
    # Admin orders a card for themself
    res = testapp.post_json("/card_order/", dict({
        "user_uuid" : admin_uuid
    }), headers=dict({
        'Authorization': "Bearer " + admin_user_token
    }), status=200)
    
    # Admin orders a card with the wrong user uuid and it fails
    res = testapp.post_json("/card_order/", dict({
        "user_uuid" : str(uuid.uuid4())
    }), headers=dict({
        'Authorization': "Bearer " + admin_user_token
    }), status=400)
    
    # Admin views all card orders, i.e the one they created
    res = testapp.get("/card_order/", headers=dict({
        'Authorization': "Bearer " + admin_user_token
    }), status=200).json_body
    assert len(res) == 1
    
    #? ---- instance.py ----
    # We get the uuid of the created order
    card_order_uuid = res[0]["uuid"]
    
    # Admin views the card order instance
    res = testapp.get(f"/card_order/{card_order_uuid}/", headers=dict({
        'Authorization': "Bearer " + admin_user_token
    }), status=200).json_body
    assert res["state"] == OrderStates.CREATED.value
    
    # Admin orders the printing of the card
    res = testapp.patch(f"/card_order/{card_order_uuid}/generate", headers=dict({
        'Authorization': "Bearer " + admin_user_token
    }), status=200)
    
    # Admin checks the order is in progress
    res = testapp.get(f"/card_order/{card_order_uuid}/", headers=dict({
        'Authorization': "Bearer " + admin_user_token
    }), status=200).json_body
    assert res["state"] == OrderStates.IN_PROGRESS.value
    
    # Admin marks the order as finished
    res = testapp.patch(f"/card_order/{card_order_uuid}/finish", headers=dict({
        'Authorization': "Bearer " + admin_user_token
    }), status=200).json_body
    assert res["state"] == OrderStates.FINISHED.value
    
    # Admin orders a new card for themself
    res = testapp.post_json("/card_order/", dict({
        "user_uuid" : admin_uuid
    }), headers=dict({
        'Authorization': "Bearer " + admin_user_token
    }), status=200).json_body
    
    card_order_uuid = res["uuid"]
    
    # Admin marks the order as cancelled
    res = testapp.delete(f"/card_order/{card_order_uuid}/cancel", headers=dict({
        'Authorization': "Bearer " + admin_user_token
    }), status=200).json_body
    assert res["state"] == OrderStates.CANCELLED.value
    
    # Admin orders the printing of the cancelled card
    res = testapp.patch(f"/card_order/{card_order_uuid}/generate", headers=dict({
        'Authorization': "Bearer " + admin_user_token
    }), status=400)
    
    # Admin views all card orders for the current event
    res = testapp.get("/card_order/", headers=dict({
        'Authorization': "Bearer " + admin_user_token
    }), status=200)
    assert len(res.json_body) == 2
    
    # Admin views all card orders for a specified event, which happens to be the current one for convenience
    current_event_uuid = testapp.get("/event/current/", status=200).json_body["uuid"]
    
    res = testapp.get(f"/card_order/", params=f"event_uuid={current_event_uuid}", headers=dict({
        'Authorization': "Bearer " + admin_user_token
    }), status=200)
    assert len(res.json_body) == 2
