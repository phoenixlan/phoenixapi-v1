from phoenixRest.models.core.event import Event
from phoenixRest.models.core.user_consent import UserConsent, ConsentType
from phoenixRest.models.core.consent_withdrawal_code import ConsentWithdrawalCode
from phoenixRest.models.core.user import User
from phoenixRest.models.crew.position import Position

from datetime import datetime

def test_consent_mail_dryrun(db, testapp):
    testapp.ensure_typical_event()

    # test is an admin
    sender_token, refresh = testapp.auth_get_tokens('test', 'sixcharacters')
    adam_token, refresh = testapp.auth_get_tokens('adam', 'sixcharacters')

    sender_user = testapp.get_user(sender_token)
    adam_user = testapp.get_user(adam_token)

    # Get how many get crew and participant mails
    crew_mail_test_pre = testapp.post_json('/email/dryrun', dict({
        'recipient_category': "crew_info",
        'subject': "hello",
        'body': "# Foo bar\nHello"
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200).json_body['count']

    participant_mail_count_pre = testapp.post_json('/email/dryrun', dict({
        'recipient_category': "participant_info",
        'subject': "hello",
        'body': "# Foo bar\nHello"
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200).json_body['count']

    # Check how many consent withdrawal codes exist
    consent_withdrawal_codes_pre = db.query(ConsentWithdrawalCode).all()

    consenting_user_result = testapp.post_json('/email/dryrun', dict({
        'recipient_category': "event_notification",
        'subject': "hello",
        'body': "# Foo bar\nHello"
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200).json_body

    assert consenting_user_result['count'] == 1 # Only the current user

    # Add record reflecting that adam consented to marketing mail
    adam_user_obj = db.query(User).filter(User.uuid == adam_user['uuid']).first()
    consent = UserConsent(adam_user_obj, ConsentType.event_notification, "test")
    db.add(consent)
    db.flush()

    # Check that the count changed
    consenting_user_result = testapp.post_json('/email/dryrun', dict({
        'recipient_category': "event_notification",
        'subject': "hello",
        'body': "# Foo bar\nHello"
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200).json_body

    assert consenting_user_result['count'] == 2 # Only the current user

    # Check that other counters didn't increase
    crew_mail_test_post = testapp.post_json('/email/dryrun', dict({
        'recipient_category': "crew_info",
        'subject': "hello",
        'body': "# Foo bar\nHello"
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200).json_body['count']

    participant_mail_count_post = testapp.post_json('/email/dryrun', dict({
        'recipient_category': "participant_info",
        'subject': "hello",
        'body': "# Foo bar\nHello"
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200).json_body['count']

    assert crew_mail_test_pre == crew_mail_test_post
    assert participant_mail_count_pre == participant_mail_count_post

    # Check how many consent codes we have now
    consent_withdrawal_codes_post = db.query(ConsentWithdrawalCode).all()

    assert len(consent_withdrawal_codes_post) == len(consent_withdrawal_codes_pre) + 1

    # Call dry run again, verify that the code count didn't change
    # We care that the consent code being used stays the same for the same recipient category
    consenting_user_result = testapp.post_json('/email/dryrun', dict({
        'recipient_category': "event_notification",
        'subject': "hello",
        'body': "# Foo bar\nHello"
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200).json_body

    assert consenting_user_result['count'] == 2 # Only the current user

    consent_withdrawal_codes_post = db.query(ConsentWithdrawalCode).all()

    assert len(consent_withdrawal_codes_post) == len(consent_withdrawal_codes_pre) + 1


def test_consent_mail_no_participants(db, testapp):
    testapp.ensure_typical_event()

    # test is an admin
    sender_token, refresh = testapp.auth_get_tokens('test', 'sixcharacters')
    adam_token, refresh = testapp.auth_get_tokens('adam', 'sixcharacters')

    sender_user = testapp.get_user(sender_token)
    adam_user = testapp.get_user(adam_token)

    consenting_user_result = testapp.post_json('/email/dryrun', dict({
        'recipient_category': "event_notification",
        'subject': "hello",
        'body': "# Foo bar\nHello"
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200).json_body

    assert consenting_user_result['count'] == 1 # Only the current user

    # Add record reflecting that adam consented to marketing mail
    adam_user_obj = db.query(User).filter(User.uuid == adam_user['uuid']).first()
    consent = UserConsent(adam_user_obj, ConsentType.event_notification, "test")
    db.add(consent)
    db.flush()

    # Check that the count changed
    consenting_user_result = testapp.post_json('/email/dryrun', dict({
        'recipient_category': "event_notification",
        'subject': "hello",
        'body': "# Foo bar\nHello"
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200).json_body

    assert consenting_user_result['count'] == 2

    # Get existing ticket types
    current_event = testapp.get('/event/current', status=200)
    res = testapp.get('/event/%s/ticketType' % current_event.json_body['uuid'], headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200)
    ticket_type = res.json_body[0]

    # Give test a free ticket. Only works because test is an admin
    res = testapp.post_json('/ticket', dict({
        'ticket_type': ticket_type['uuid'],
        'recipient': adam_user['uuid']
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200)

    # Call the dry run again. As adam is now a participant, they should not get an e-mail
    consenting_user_result = testapp.post_json('/email/dryrun', dict({
        'recipient_category': "event_notification",
        'subject': "hello",
        'body': "# Foo bar\nHello"
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200).json_body

    assert consenting_user_result['count'] == 1


def test_consent_mail_no_crew(db, testapp):
    testapp.ensure_typical_event()

    # test is an admin
    sender_token, refresh = testapp.auth_get_tokens('test', 'sixcharacters')
    adam_token, refresh = testapp.auth_get_tokens('adam', 'sixcharacters')

    sender_user = testapp.get_user(sender_token)
    adam_user = testapp.get_user(adam_token)

    consenting_user_result = testapp.post_json('/email/dryrun', dict({
        'recipient_category': "event_notification",
        'subject': "hello",
        'body': "# Foo bar\nHello"
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200).json_body

    assert consenting_user_result['count'] == 1 # Only the current user

    # Add record reflecting that adam consented to marketing mail
    adam_user_obj = db.query(User).filter(User.uuid == adam_user['uuid']).first()
    consent = UserConsent(adam_user_obj, ConsentType.event_notification, "test")
    db.add(consent)
    db.flush()

    # Check that the count changed
    consenting_user_result = testapp.post_json('/email/dryrun', dict({
        'recipient_category': "event_notification",
        'subject': "hello",
        'body': "# Foo bar\nHello"
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200).json_body

    assert consenting_user_result['count'] == 2

    position_candidates = list(
        filter(lambda position: position['crew_uuid'] is not None, testapp.get('/position', headers=dict({
            "Authorization": "Bearer " + sender_token
        }), status=200).json_body)
    )

    created_mapping = testapp.post_json('/position_mapping', {
        "position_uuid": position_candidates[0]['uuid'],
        "user_uuid": adam_user['uuid']
    }, headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200).json_body

    assert created_mapping['uuid'] != None

    # Call the dry run again. As adam is now a crew member, they should not get an e-mail
    consenting_user_result = testapp.post_json('/email/dryrun', dict({
        'recipient_category': "event_notification",
        'subject': "hello",
        'body': "# Foo bar\nHello"
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200).json_body

    assert consenting_user_result['count'] == 1


def test_consent_mail_no_applicants(db, testapp):
    testapp.ensure_typical_event()

    # test is an admin
    sender_token, refresh = testapp.auth_get_tokens('test', 'sixcharacters')
    adam_token, refresh = testapp.auth_get_tokens('adam', 'sixcharacters')

    sender_user = testapp.get_user(sender_token)
    adam_user = testapp.get_user(adam_token)

    consenting_user_result = testapp.post_json('/email/dryrun', dict({
        'recipient_category': "event_notification",
        'subject': "hello",
        'body': "# Foo bar\nHello"
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200).json_body

    assert consenting_user_result['count'] == 1 # Only the current user

    # Add record reflecting that adam consented to marketing mail
    adam_user_obj = db.query(User).filter(User.uuid == adam_user['uuid']).first()
    consent = UserConsent(adam_user_obj, ConsentType.event_notification, "test")
    db.add(consent)
    db.flush()

    # Check that the count changed
    consenting_user_result = testapp.post_json('/email/dryrun', dict({
        'recipient_category': "event_notification",
        'subject': "hello",
        'body': "# Foo bar\nHello"
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200).json_body

    assert consenting_user_result['count'] == 2

    current_event = testapp.get('/event/current', status=200).json_body
    testapp.post('/user/%s/avatar' % adam_user['uuid'], params="x=%d&y=%d&w=%d&h=%d"% (0, 0, 600, 450), upload_files=[('file', "phoenixRest/tests/assets/avatar_test.png")], headers=dict({
        "Authorization": "Bearer " + adam_token
    }), status = 200)

    application_crews = list(filter(lambda crew: crew["is_applyable"], testapp.get('/crew', status=200).json_body))

    res = testapp.put_json('/application', dict({
        'crews': [application_crews[0]['uuid']],
        'contents': 'I want to join please'
    }), headers=dict({
        "Authorization": "Bearer " + adam_token
    }), status=200)

    # Call the dry run again. As adam is now a crew member, they should not get an e-mail
    consenting_user_result = testapp.post_json('/email/dryrun', dict({
        'recipient_category': "event_notification",
        'subject': "hello",
        'body': "# Foo bar\nHello"
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200).json_body

    assert consenting_user_result['count'] == 1

