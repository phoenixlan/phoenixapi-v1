from test_app import TestApp

NORMAL_AVATAR = "phoenixRest/tests/assets/avatar_test.png"
TRANSPARENT_AVATAR = "phoenixRest/tests/assets/transparent.png"

def test_upload_avatar(testapp:TestApp):
    testapp.upload_avatar("test@example.com", "sixcharacters", NORMAL_AVATAR, 10, 10, 600, 450)

def test_upload_transparent_avatar(testapp:TestApp):
    testapp.upload_avatar("test@example.com", "sixcharacters", TRANSPARENT_AVATAR, 10, 10, 600, 450)

def test_upload_avatar_bad_bounds(testapp:TestApp):
    # Ensure the minimum requirements are held
    testapp.upload_avatar("test@example.com", "sixcharacters", TRANSPARENT_AVATAR, 10, 10, 10, 450, expected_status=400)
    testapp.upload_avatar("test@example.com", "sixcharacters", TRANSPARENT_AVATAR, 10, 10, 600, 10, expected_status=400)

    # Ensure that when the bounds are outside the image, the site complains
    testapp.upload_avatar("test@example.com", "sixcharacters", TRANSPARENT_AVATAR, 10, 10, 1000, 1000, expected_status=400)

    # Ensure that when the bounding box starts outside the image, the site complains
    testapp.upload_avatar("test@example.com", "sixcharacters", TRANSPARENT_AVATAR, 1000, 1000, 600, 450, expected_status=400)    
