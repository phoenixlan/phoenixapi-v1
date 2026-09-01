import uuid


def test_crew_card_for_event_member(testapp, upcoming_event, chief_user, admin_token):
    """A crew card can be fetched for a user holding a position at the event"""
    # The user needs an avatar for the card to be drawn
    chief_token, refresh = testapp.auth_get_tokens(chief_user.email, 'sixcharacters')
    testapp.upload_avatar(
        chief_token, 'phoenixRest/tests/assets/avatar_test.png', 10, 10, 600, 450,
        expected_status=200
    )

    res = testapp.get('/event/%s/crew_card?user_uuid=%s' % (upcoming_event.uuid, chief_user.uuid), headers=dict({
        'Authorization': "Bearer " + admin_token
    }), status=200)

    assert res.content_type == 'image/png'
    assert len(res.body) > 0


def test_crew_card_requires_user_uuid(testapp, upcoming_event, admin_token):
    """user_uuid is a required get parameter"""
    testapp.get('/event/%s/crew_card' % upcoming_event.uuid, headers=dict({
        'Authorization': "Bearer " + admin_token
    }), status=400)


def test_crew_card_unknown_user(testapp, upcoming_event, admin_token):
    """A user_uuid nobody owns is rejected"""
    testapp.get('/event/%s/crew_card?user_uuid=%s' % (upcoming_event.uuid, uuid.uuid4()), headers=dict({
        'Authorization': "Bearer " + admin_token
    }), status=400)


def test_crew_card_user_not_part_of_event(testapp, upcoming_event, adam_user, admin_token):
    """A user without a position at the event does not get a crew card"""
    res = testapp.get('/event/%s/crew_card?user_uuid=%s' % (upcoming_event.uuid, adam_user.uuid), headers=dict({
        'Authorization': "Bearer " + admin_token
    }), status=400)

    assert 'does not belong to this event' in res.text


def test_crew_card_user_from_other_brand(testapp, other_upcoming_event, chief_user, admin_token):
    """A position at one brand's event does not grant a crew card for another brand's event"""
    testapp.get('/event/%s/crew_card?user_uuid=%s' % (other_upcoming_event.uuid, chief_user.uuid), headers=dict({
        'Authorization': "Bearer " + admin_token
    }), status=400)


def test_crew_card_as_chief(testapp, upcoming_event, chief_user, greg_user):
    """A chief can fetch the crew card of someone at their brand's event"""
    chief_token, refresh = testapp.auth_get_tokens(chief_user.email, 'sixcharacters')

    # The user needs an avatar for the card to be drawn
    greg_token, refresh = testapp.auth_get_tokens(greg_user.email, 'sixcharacters')
    testapp.upload_avatar(
        greg_token, 'phoenixRest/tests/assets/avatar_test.png', 10, 10, 600, 450,
        expected_status=200
    )

    res = testapp.get('/event/%s/crew_card?user_uuid=%s' % (upcoming_event.uuid, greg_user.uuid), headers=dict({
        'Authorization': "Bearer " + chief_token
    }), status=200)

    assert res.content_type == 'image/png'
    assert len(res.body) > 0


def test_crew_card_forbidden_for_regular_user(testapp, upcoming_event, chief_user, jeff_user):
    """Ordinary crew members can't fetch crew cards"""
    token, refresh = testapp.auth_get_tokens(jeff_user.email, 'sixcharacters')

    testapp.get('/event/%s/crew_card?user_uuid=%s' % (upcoming_event.uuid, chief_user.uuid), headers=dict({
        'Authorization': "Bearer " + token
    }), status=403)
