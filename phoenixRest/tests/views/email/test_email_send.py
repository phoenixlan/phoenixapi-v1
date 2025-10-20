
from phoenixRest.models.core.user import User
from phoenixRest.models.core.user_consent import UserConsent, ConsentType

def test_crew_mail_sending(testapp, upcoming_event):
    testapp.ensure_typical_event()

    sender_token, refresh = testapp.auth_get_tokens('test@example.com', 'sixcharacters')

    crew_mail_test = testapp.post_json('/email/send', dict({
        'recipient_category': "crew_info",
        'subject': "hello",
        'body': "# Foo bar\nHello"
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200).json_body

    assert crew_mail_test['sent'] == 3 # The user is a crew member already

def test_participant_mail_sending(testapp, upcoming_event):
    testapp.ensure_typical_event()

    sender_token, refresh = testapp.auth_get_tokens('test@example.com', 'sixcharacters')

    crew_mail_test = testapp.post_json('/email/send', dict({
        'recipient_category': "participant_info",
        'subject': "hello",
        'body': "# Foo bar\nHello"
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200).json_body

    assert crew_mail_test['sent'] == 1

def test_consent_mail_sending(db, testapp, upcoming_event):
    testapp.ensure_typical_event()

    sender_token, refresh = testapp.auth_get_tokens('test@example.com', 'sixcharacters')
    adam_token, refresh = testapp.auth_get_tokens('adam@example.com', 'sixcharacters')

    adam_user = testapp.get_user(adam_token)

    # Add record reflecting that Jeff consented to marketing mail
    adam_user_obj = db.query(User).filter(User.uuid == adam_user['uuid']).first()
    consent = UserConsent(adam_user_obj, ConsentType.event_notification, "test")
    db.add(consent)
    db.flush()

    consent_mail_test = testapp.post_json('/email/send', dict({
        'recipient_category': "event_notification",
        'subject': "hello",
        'body': "# Foo bar\nHello"
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200).json_body

    assert consent_mail_test['sent'] == 2

def test_invalid_mail_category_send(testapp, upcoming_event):
    testapp.ensure_typical_event()

    # test is an admin
    sender_token, refresh = testapp.auth_get_tokens('test@example.com', 'sixcharacters')

    target_users = testapp.post_json('/email/send', dict({
        'recipient_category': "swag",
        'subject': "hello",
        'body': "# Foo bar\nHello"
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=400)
