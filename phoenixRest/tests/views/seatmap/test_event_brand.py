from phoenixRest.models.core.event_brand import EventBrand


def test_seatmaps_are_listed_only_for_their_event_brand(
        testapp, db, event_brand, admin_token):
    other_brand = EventBrand('Other event brand')
    db.add(other_brand)
    db.flush()

    headers = {
        'Authorization': "Bearer " + admin_token
    }

    seatmap = testapp.put_json('/seatmap', {
        'name': 'Main hall',
        'description': 'Owned by the fixture brand',
        'event_brand_uuid': str(event_brand.uuid)
    }, headers=headers, status=200).json_body

    other_seatmap = testapp.put_json('/seatmap', {
        'name': 'Side hall',
        'description': 'Owned by the other brand',
        'event_brand_uuid': str(other_brand.uuid)
    }, headers=headers, status=200).json_body

    brand_seatmaps = testapp.get(
        '/event_brand/%s/seatmap' % event_brand.uuid,
        headers=headers,
        status=200
    ).json_body
    other_brand_seatmaps = testapp.get(
        '/event_brand/%s/seatmap' % other_brand.uuid,
        headers=headers,
        status=200
    ).json_body

    assert [entry['uuid'] for entry in brand_seatmaps] == [seatmap['uuid']]
    assert [entry['uuid'] for entry in other_brand_seatmaps] == [other_seatmap['uuid']]
