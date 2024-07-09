from phoenixRest.tests.test_app import TestApp

NORMAL_AVATAR_JPEG = "phoenixRest/tests/assets/avatar_test.jpg"
NORMAL_AVATAR_PNG = "phoenixRest/tests/assets/avatar_test.png"
TRANSPARENT_AVATAR_PNG_RGBA = "phoenixRest/tests/assets/transparent_rgba.png"
TRANSPARENT_AVATAR_PNG_P = "phoenixRest/tests/assets/transparent_p.png"
TRANSPARENT_AVATAR_PNG_RGBA_P = "phoenixRest/tests/assets/transparent_rgba_p.png"

def upload_avatar_test_helper(testapp:TestApp, token, path, x,y, w,h, expected_status=None):
    # We upload the avatar with the expected status
    avatar_uuid = testapp.upload_avatar(token, path, x,y, w,h, expected_status=expected_status)
    
    # If we expect a successful upload we need to delete it afterwards
    if expected_status == 200:
        testapp.delete(f"/avatar/{avatar_uuid}/", headers=dict({
            "Authorization": "Bearer " + token
        }), status=200)

def test_upload_avatar_jpg(testapp:TestApp):
    test_user_token, refresh = testapp.auth_get_tokens("test@example.com", "sixcharacters")
    upload_avatar_test_helper(testapp, test_user_token, NORMAL_AVATAR_JPEG, 10, 10, 600, 450, expected_status=200)
    
def test_upload_avatar_png(testapp:TestApp):
    test_user_token, refresh = testapp.auth_get_tokens("test@example.com", "sixcharacters")
    upload_avatar_test_helper(testapp, test_user_token, NORMAL_AVATAR_PNG, 10, 10, 600, 450, expected_status=200)

def test_upload_avatar_transparent_rgba(testapp:TestApp):
    test_user_token, refresh = testapp.auth_get_tokens("test@example.com", "sixcharacters")
    upload_avatar_test_helper(testapp, test_user_token, TRANSPARENT_AVATAR_PNG_RGBA, 10, 10, 600, 450, expected_status=200)
    
def test_upload_avatar_transparent_p(testapp:TestApp):
    test_user_token, refresh = testapp.auth_get_tokens("test@example.com", "sixcharacters")                                
    upload_avatar_test_helper(testapp, test_user_token, TRANSPARENT_AVATAR_PNG_P, 10, 10, 600, 450, expected_status=200)
    
def test_upload_avatar_transparent_rgba_p(testapp:TestApp):
    test_user_token, refresh = testapp.auth_get_tokens("test@example.com", "sixcharacters")
    upload_avatar_test_helper(testapp, test_user_token, TRANSPARENT_AVATAR_PNG_RGBA_P, 10, 10, 600, 450, expected_status=200)

def test_upload_avatar_bad_bounds(testapp:TestApp):
    test_user_token, refresh = testapp.auth_get_tokens("test@example.com", "sixcharacters")
    
    # Ensure the minimum requirements are held
    upload_avatar_test_helper(testapp, test_user_token, TRANSPARENT_AVATAR_PNG_RGBA, 10, 10, 10, 450, expected_status=400)
    upload_avatar_test_helper(testapp, test_user_token, TRANSPARENT_AVATAR_PNG_RGBA, 10, 10, 600, 10, expected_status=400)

    # Ensure that when the bounds are outside the image, the site complains
    upload_avatar_test_helper(testapp, test_user_token, TRANSPARENT_AVATAR_PNG_RGBA, 10, 10, 1000, 1000, expected_status=400)

    # Ensure that when the bounding box starts outside the image, the site complains
    upload_avatar_test_helper(testapp, test_user_token, TRANSPARENT_AVATAR_PNG_RGBA, 1000, 1000, 600, 450, expected_status=400)
