NORMAL_JPEG = "phoenixRest/tests/assets/avatar_test.jpg"
NORMAL_PNG = "phoenixRest/tests/assets/avatar_test.png"
NORMAL_TGA = "phoenixRest/tests/assets/avatar_test.tga"

def test_upload_background_jpg(testapp, event_brand, admin_token):
    headers = {
        'Authorization': "Bearer " + admin_token
    }
    seatmap = testapp.put_json('/seatmap', {
        'name': 'Main hall',
        'description': 'Main hall seating',
        'event_brand_uuid': str(event_brand.uuid)
    }, headers=headers, status=200).json_body

    testapp.put('/seatmap/%s/background' % seatmap['uuid'], upload_files=[
        ('file', NORMAL_JPEG)
    ], headers=headers, status=200)

    seatmap = testapp.get('/seatmap/%s' % seatmap['uuid'], headers=headers, status=200).json_body
    assert seatmap['background']['url'].endswith('.jpg')

def test_upload_background_non_image_disguised_as_png(testapp, event_brand, admin_token):
    headers = {
        'Authorization': "Bearer " + admin_token
    }
    seatmap = testapp.put_json('/seatmap', {
        'name': 'Main hall',
        'description': 'Main hall seating',
        'event_brand_uuid': str(event_brand.uuid)
    }, headers=headers, status=200).json_body

    # The .png name gets past the extension check, so the file content itself must be rejected
    with open(NORMAL_TGA, "rb") as f:
        testapp.put('/seatmap/%s/background' % seatmap['uuid'], upload_files=[
            ('file', 'background.png', f.read())
        ], headers=headers, status=400)

    seatmap = testapp.get('/seatmap/%s' % seatmap['uuid'], headers=headers, status=200).json_body
    assert seatmap['background'] is None

def test_upload_background_invalid_extension(testapp, event_brand, admin_token):
    headers = {
        'Authorization': "Bearer " + admin_token
    }
    seatmap = testapp.put_json('/seatmap', {
        'name': 'Main hall',
        'description': 'Main hall seating',
        'event_brand_uuid': str(event_brand.uuid)
    }, headers=headers, status=200).json_body

    # A valid image is still rejected when it is named as another file type
    with open(NORMAL_PNG, "rb") as f:
        testapp.put('/seatmap/%s/background' % seatmap['uuid'], upload_files=[
            ('file', 'background.svg', f.read())
        ], headers=headers, status=400)

    seatmap = testapp.get('/seatmap/%s' % seatmap['uuid'], headers=headers, status=200).json_body
    assert seatmap['background'] is None
