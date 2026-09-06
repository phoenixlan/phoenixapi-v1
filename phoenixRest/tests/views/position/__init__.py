def _position_payload(**overrides):
    payload = {
        'name': 'Test position',
        'description': 'Position ownership test',
        'chief': False,
        'is_vanity': False,
        'crew_uuid': None,
        'team_uuid': None
    }
    payload.update(overrides)
    return payload


def test_create_positions_assigns_event_brand(
        testapp, event_brand, testcrew, testteam, admin_token):
    headers = {'Authorization': "Bearer " + admin_token}

    crew_position = testapp.post_json('/position', _position_payload(
        name='Crew position', crew_uuid=str(testcrew.uuid)
    ), headers=headers, status=200).json_body
    assert crew_position['event_brand_uuid'] == str(event_brand.uuid)
    assert crew_position['crew_uuid'] == str(testcrew.uuid)

    team_position = testapp.post_json('/position', _position_payload(
        name='Team position', team_uuid=str(testteam.uuid)
    ), headers=headers, status=200).json_body
    assert team_position['event_brand_uuid'] == str(event_brand.uuid)
    assert team_position['crew_uuid'] == str(testcrew.uuid)
    assert team_position['team_uuid'] == str(testteam.uuid)

    brand_position = testapp.post_json('/position', _position_payload(
        name='Standalone position', event_brand_uuid=str(event_brand.uuid)
    ), headers=headers, status=200).json_body
    assert brand_position['event_brand_uuid'] == str(event_brand.uuid)


def test_create_position_rejects_conflicting_ownership(
        testapp, testcrew, other_team, other_event_brand, admin_token):
    headers = {'Authorization': "Bearer " + admin_token}

    response = testapp.post_json('/position', _position_payload(
        crew_uuid=str(testcrew.uuid), team_uuid=str(other_team.uuid)
    ), headers=headers, status=400)
    assert response.json_body['error'] == 'Team belongs to a different crew'

    response = testapp.post_json('/position', _position_payload(
        crew_uuid=str(testcrew.uuid),
        event_brand_uuid=str(other_event_brand.uuid)
    ), headers=headers, status=400)
    assert response.json_body['error'] == \
        'Crew or team belongs to a different event brand'
