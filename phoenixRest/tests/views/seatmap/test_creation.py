def test_create_seatmap_with_row_and_seats(testapp, event_brand, admin_token):
    headers = {
        'Authorization': "Bearer " + admin_token
    }

    seatmap = testapp.put_json('/seatmap', {
        'name': 'Main hall',
        'description': 'Main hall seating',
        'event_brand_uuid': str(event_brand.uuid)
    }, headers=headers, status=200).json_body

    assert seatmap['name'] == 'Main hall'
    assert seatmap['description'] == 'Main hall seating'
    assert seatmap['event_brand_uuid'] == str(event_brand.uuid)
    assert seatmap['rows'] == []

    row = testapp.put_json('/seatmap/%s/row' % seatmap['uuid'], {
        'row_number': 1,
        'x': 10,
        'y': 20,
        'horizontal': True
    }, headers=headers, status=200).json_body

    assert row['seatmap_uuid'] == seatmap['uuid']
    assert row['row_number'] == 1
    assert row['x'] == 10
    assert row['y'] == 20
    assert row['is_horizontal'] is True
    assert row['seats'] == []

    seats = []
    for expected_number in range(1, 4):
        seat = testapp.put_json('/row/%s/seat' % row['uuid'], {},
            headers=headers, status=200).json_body
        assert seat['row_uuid'] == row['uuid']
        assert seat['number'] == expected_number
        seats.append(seat)

    fetched_seatmap = testapp.get('/seatmap/%s' % seatmap['uuid'],
        headers=headers, status=200).json_body

    assert len(fetched_seatmap['rows']) == 1
    assert fetched_seatmap['rows'][0]['uuid'] == row['uuid']
    assert [seat['uuid'] for seat in fetched_seatmap['rows'][0]['seats']] == [
        seat['uuid'] for seat in seats
    ]
    assert [seat['number'] for seat in fetched_seatmap['rows'][0]['seats']] == [1, 2, 3]
