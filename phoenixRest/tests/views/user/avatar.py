from phoenixRest.tests.test_app import TestApp

NORMAL_AVATAR = "phoenixRest/tests/assets/avatar_test.png"
TRANSPARENT_AVATAR = "phoenixRest/tests/assets/transparent.png"

def upload_avatar_test_helper(testapp:TestApp, token, path, x,y, w,h, expected_status=None):
    # We upload the avatar with the expected status
    avatar_uuid = testapp.upload_avatar(token, path, x,y, w,h, expected_status=expected_status)
    
    # If we expect a successful upload we need to delete it afterwards
    if expected_status == 200:
        testapp.delete(f"/avatar/{avatar_uuid}/", headers=dict({
            "Authorization": "Bearer " + token
        }), status=200)

def test_upload_avatar(testapp:TestApp):
    test_user_token, refresh = testapp.auth_get_tokens("test@example.com", "sixcharacters")
    
    upload_avatar_test_helper(testapp, test_user_token, NORMAL_AVATAR, 10, 10, 600, 450, expected_status=200)

def test_upload_transparent_avatar(testapp:TestApp):
    test_user_token, refresh = testapp.auth_get_tokens("test@example.com", "sixcharacters")
    upload_avatar_test_helper(testapp, test_user_token, TRANSPARENT_AVATAR, 10, 10, 600, 450, expected_status=200)

def test_upload_avatar_bad_bounds(testapp:TestApp):
    test_user_token, refresh = testapp.auth_get_tokens("test@example.com", "sixcharacters")
    
    # Ensure the minimum requirements are held
    upload_avatar_test_helper(testapp, test_user_token, TRANSPARENT_AVATAR, 10, 10, 10, 450, expected_status=400)
    upload_avatar_test_helper(testapp, test_user_token, TRANSPARENT_AVATAR, 10, 10, 600, 10, expected_status=400)

    # Ensure that when the bounds are outside the image, the site complains
    upload_avatar_test_helper(testapp, test_user_token, TRANSPARENT_AVATAR, 10, 10, 1000, 1000, expected_status=400)

    # Ensure that when the bounding box starts outside the image, the site complains
    upload_avatar_test_helper(testapp, test_user_token, TRANSPARENT_AVATAR, 1000, 1000, 600, 450, expected_status=400)
