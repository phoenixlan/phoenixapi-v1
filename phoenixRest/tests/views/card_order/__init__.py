from test_app import TestApp
import uuid
from phoenixRest.models.crew.card_order import OrderStates

def test_card_order(testapp:TestApp, upcoming_event, admin_user, brand_admin_user):
    # Log in as an admin user
    admin_user_token, refresh = testapp.auth_get_tokens(admin_user.email, "sixcharacters")
    admin = testapp.get_user(admin_user_token)
    admin_uuid = admin["uuid"]

    # Log in as an brand admin user
    brand_admin_user_token, refresh = testapp.auth_get_tokens(brand_admin_user.email, "sixcharacters")
    brand_admin = testapp.get_user(brand_admin_user_token)
    brand_admin_uuid = brand_admin["uuid"]
    
    # We ensure that admin has an avatar
    testapp.upload_avatar(admin_user_token, "phoenixRest/tests/assets/avatar_test.png", 10, 10, 600, 450, expected_status=200)
    testapp.upload_avatar(brand_admin_user_token, "phoenixRest/tests/assets/avatar_test.png", 10, 10, 600, 450, expected_status=200)
    
    #? ---- __init__.py ----
    # Admin orders a card for themself
    res = testapp.post_json("/event/%s/card_order" % upcoming_event.uuid, dict({
        "user_uuid" : admin_uuid
    }), headers=dict({
        'Authorization': "Bearer " + admin_user_token
    }), status=200)

    # Brand admin orders a card for themself
    res = testapp.post_json("/event/%s/card_order" % upcoming_event.uuid, dict({
        "user_uuid" : brand_admin_uuid
    }), headers=dict({
        'Authorization': "Bearer " + brand_admin_user_token
    }), status=200)

    
    # Admin orders a card with the wrong user uuid and it fails
    res = testapp.post_json("/event/%s/card_order" % upcoming_event.uuid, dict({
        "user_uuid" : str(uuid.uuid4())
    }), headers=dict({
        'Authorization': "Bearer " + admin_user_token
    }), status=400)

    # Brand admin orders a card with the wrong user uuid and it fails
    res = testapp.post_json("/event/%s/card_order" % upcoming_event.uuid, dict({
        "user_uuid" : str(uuid.uuid4())
    }), headers=dict({
        'Authorization': "Bearer " + brand_admin_user_token
    }), status=400)
    
    # Admin views all card orders, i.e the one they created
    res = testapp.get(f"/event/{upcoming_event.uuid}/card_orders", headers=dict({
        'Authorization': "Bearer " + admin_user_token
    }), status=200).json_body
    assert len(res) == 2

    # Brand admin views all card orders, i.e. the one they created
    res = testapp.get(f"/event/{upcoming_event.uuid}/card_orders", headers=dict({
        'Authorization': "Bearer " + brand_admin_user_token
    }), status=200).json_body
    assert len(res) == 2
    
    #? ---- instance.py ----
    # We get the uuid of the created order
    card_order_uuid = res[0]["uuid"]
    
    # Admin views the card order instance
    res = testapp.get(f"/card_order/{card_order_uuid}/", headers=dict({
        'Authorization': "Bearer " + admin_user_token
    }), status=200).json_body
    assert res["state"] == OrderStates.CREATED.value

    # Brand admin views the card order interface
    res = testapp.get(f"/card_order/{card_order_uuid}/", headers=dict({
        'Authorization': "Bearer " + brand_admin_user_token
    }), status=200).json_body
    assert res["state"] == OrderStates.CREATED.value
    
    # Admin orders the printing of the card
    res = testapp.patch(f"/card_order/{card_order_uuid}/generate", headers=dict({
        'Authorization': "Bearer " + admin_user_token
    }), status=200)

    # Brand admin orders the printing of the card
    res = testapp.patch(f"/card_order/{card_order_uuid}/generate", headers=dict({
        'Authorization': "Bearer " + brand_admin_user_token
    }), status=200)
    
    # Admin checks the order is in progress
    res = testapp.get(f"/card_order/{card_order_uuid}/", headers=dict({
        'Authorization': "Bearer " + admin_user_token
    }), status=200).json_body
    assert res["state"] == OrderStates.IN_PROGRESS.value

    # Brand admin checks the order is in progress
    res = testapp.get(f"/card_order/{card_order_uuid}/", headers=dict({
        'Authorization': "Bearer " + brand_admin_user_token
    }), status=200).json_body
    assert res["state"] == OrderStates.IN_PROGRESS.value
    
    # Admin marks the order as finished
    res = testapp.patch(f"/card_order/{card_order_uuid}/finish", headers=dict({
        'Authorization': "Bearer " + admin_user_token
    }), status=200).json_body
    assert res["state"] == OrderStates.FINISHED.value

    # Brand admin marks the order as finished
    res = testapp.patch(f"/card_order/{card_order_uuid}/finish", headers=dict({
        'Authorization': "Bearer " + brand_admin_user_token
    }), status=200).json_body
    assert res["state"] == OrderStates.FINISHED.value

    # Admin orders a new card for themself
    res = testapp.post_json("/event/%s/card_order" % upcoming_event.uuid, dict({
        "user_uuid" : admin_uuid
    }), headers=dict({
        'Authorization': "Bearer " + admin_user_token
    }), status=200).json_body

    # Brand admin orders a new card for themself
    res = testapp.post_json("/event/%s/card_order" % upcoming_event.uuid, dict({
        "user_uuid" : brand_admin_uuid
    }), headers=dict({
        'Authorization': "Bearer " + brand_admin_user_token
    }), status=200).json_body
    
    card_order_uuid = res["uuid"]
    
    # Admin marks the order as cancelled
    res = testapp.delete(f"/card_order/{card_order_uuid}/cancel", headers=dict({
        'Authorization': "Bearer " + admin_user_token
    }), status=200).json_body
    assert res["state"] == OrderStates.CANCELLED.value

    # Brand admin marks the order as cancelled
    res = testapp.delete(f"/card_order/{card_order_uuid}/cancel", headers=dict({
        'Authorization': "Bearer " + brand_admin_user_token
    }), status=200).json_body
    assert res["state"] == OrderStates.CANCELLED.value
    
    # Admin orders the printing of the cancelled card
    res = testapp.patch(f"/card_order/{card_order_uuid}/generate", headers=dict({
        'Authorization': "Bearer " + admin_user_token
    }), status=400)

    # Brand admin orders the printing of the cancelled card
    res = testapp.patch(f"/card_order/{card_order_uuid}/generate", headers=dict({
        'Authorization': "Bearer " + brand_admin_user_token
    }), status=400)
    
    # Admin views all card orders for the current event
    res = testapp.get(f"/event/{upcoming_event.uuid}/card_orders", headers=dict({
        'Authorization': "Bearer " + admin_user_token
    }), status=200)
    assert len(res.json_body) == 4

    # Brand admin views all card orders for the current event
    res = testapp.get(f"/event/{upcoming_event.uuid}/card_orders", headers=dict({
        'Authorization': "Bearer " + brand_admin_user_token
    }), status=200)
    assert len(res.json_body) == 4

def test_chief_can_create_card_order_only_for_own_brand(
        testapp, upcoming_event, other_upcoming_event, chief_user, brand_admin_user):
    token, refresh = testapp.auth_get_tokens(chief_user.email, 'sixcharacters')
    brand_admin_token, refresh = testapp.auth_get_tokens(brand_admin_user.email, 'sixcharacters')

    testapp.post_json('/event/%s/card_order' % upcoming_event.uuid, {
        'user_uuid': str(chief_user.uuid)
    }, headers={
        'Authorization': "Bearer " + token
    }, status=200)

    testapp.post_json('/event/%s/card_order' % other_upcoming_event.uuid, {
        'user_uuid': str(chief_user.uuid)
    }, headers={
        'Authorization': "Bearer " + token
    }, status=403)

    testapp.post_json('/event/%s/card_order' % upcoming_event.uuid, {
        'user_uuid': str(brand_admin_user.uuid)
    }, headers={
        'Authorization': "Bearer " + brand_admin_token
    }, status=200)

    testapp.post_json('/event/%s/card_order' % other_upcoming_event.uuid, {
        'user_uuid': str(brand_admin_user.uuid)
    }, headers={
        'Authorization': "Bearer " + brand_admin_token
    }, status=403)
    
