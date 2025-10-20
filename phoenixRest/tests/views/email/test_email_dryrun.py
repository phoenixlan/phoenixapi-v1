from phoenixRest.models.core.event import Event
from phoenixRest.models.core.user_consent import UserConsent, ConsentType
from phoenixRest.models.core.consent_withdrawal_code import ConsentWithdrawalCode
from phoenixRest.models.core.user import User
from phoenixRest.models.crew.position import Position

def test_crew_mail_dryryn(db, testapp, upcoming_event):
    """Tests that crew members receive mail when the crew_info category is used.
    Participants should not receive these mails.
    
    Assumes nobody has consented to marketing mail"""
    testapp.ensure_typical_event()

    # test is an admin
    sender_token, refresh = testapp.auth_get_tokens('test@example.com', 'sixcharacters')
    adam_token, refresh = testapp.auth_get_tokens('adam@example.com', 'sixcharacters')

    sender_user = testapp.get_user(sender_token)
    adam_user = testapp.get_user(adam_token)

    # Check how many participants we are mailing
    participant_mail_count_pre = testapp.post_json('/email/dryrun', dict({
        'recipient_category': "participant_info",
        'subject': "hello",
        'body': "# Foo bar\nHello"
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200).json_body['count']
    # Check how many consenting users we would be mailing
    consenting_user_pre = testapp.post_json('/email/dryrun', dict({
        'recipient_category': "event_notification",
        'subject': "hello",
        'body': "# Foo bar\nHello"
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200).json_body['count']

    # Test email sending to crews
    crew_mail_test = testapp.post_json('/email/dryrun', dict({
        'recipient_category': "crew_info",
        'subject': "hello",
        'body': "# Foo bar\nHello"
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200).json_body

    assert crew_mail_test['count'] == 3 # The user is a crew member already

    # Give adam a position with no crew attachment, and verify that the count does not increase
    position = db.query(Position).filter(Position.crew_uuid == None).first()
    mapping = testapp.post_json('/position_mapping', dict({
        "user_uuid": adam_user['uuid'],
        "position_uuid": str(position.uuid)
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200)

    crew_mail_test = testapp.post_json('/email/dryrun', dict({
        'recipient_category': "crew_info",
        'subject': "hello",
        'body': "# Foo bar\nHello"
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200).json_body

    assert crew_mail_test['count'] == 3 # The number should increase to reflect that adam now is a crew

    # Add adam to a crew, and see that the count increases
    # Get a position with a connected crew
    position = db.query(Position).filter(Position.crew_uuid != None).first()

    # Create a position mapping
    mapping = testapp.post_json('/position_mapping', dict({
        "user_uuid": adam_user['uuid'],
        "position_uuid": str(position.uuid)
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200)

    crew_mail_test = testapp.post_json('/email/dryrun', dict({
        'recipient_category': "crew_info",
        'subject': "hello",
        'body': "# Foo bar\nHello"
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200).json_body

    assert crew_mail_test['count'] == 4 # The number should increase to reflect that adam now is a crew

    # Check that the participant list hasn't increased
    participant_mail_count_post = testapp.post_json('/email/dryrun', dict({
        'recipient_category': "participant_info",
        'subject': "hello",
        'body': "# Foo bar\nHello"
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200).json_body['count']
    consenting_user_post = testapp.post_json('/email/dryrun', dict({
        'recipient_category': "event_notification",
        'subject': "hello",
        'body': "# Foo bar\nHello"
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200).json_body['count']

    assert participant_mail_count_pre == participant_mail_count_post
    assert consenting_user_pre == consenting_user_post


def test_participant_mail_dryrun(testapp, upcoming_event):
    """Tests that all participants get e-mails when the participant_info category is used.
    Crew members should not receive these mails if they don't have a ticket
    
    Assumes nobody has consented to marketing mail"""
    testapp.ensure_typical_event()

    # test is an admin
    sender_token, refresh = testapp.auth_get_tokens('test@example.com', 'sixcharacters')
    adam_token, refresh = testapp.auth_get_tokens('adam@example.com', 'sixcharacters')

    sender_user = testapp.get_user(sender_token)
    adam_user = testapp.get_user(adam_token)

    participant_mail_test_results = testapp.post_json('/email/dryrun', dict({
        'recipient_category': "participant_info",
        'subject': "hello",
        'body': "# Foo bar\nHello"
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200).json_body

    assert participant_mail_test_results['count'] == 1 # Only the current user

    # Get the number of crew mail recipients
    crew_mail_test_pre = testapp.post_json('/email/dryrun', dict({
        'recipient_category': "crew_info",
        'subject': "hello",
        'body': "# Foo bar\nHello"
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200).json_body['count']
    consenting_user_pre = testapp.post_json('/email/dryrun', dict({
        'recipient_category': "event_notification",
        'subject': "hello",
        'body': "# Foo bar\nHello"
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200).json_body['count']


    # Now give adam a free ticket
    current_event = testapp.get('/event/current', status=200)
    # Get existing ticket types
    res = testapp.get('/event/%s/ticketType' % current_event.json_body['uuid'], headers=dict({
        "Authorization": "Bearer " + sender_token 
    }), status=200)
    ticket_type = res.json_body[0]

    res = testapp.post_json('/ticket', dict({
        'ticket_type': ticket_type['uuid'],
        'recipient': adam_user['uuid']
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200)

    # The number of participants should change
    participant_mail_test_results = testapp.post_json('/email/dryrun', dict({
        'recipient_category': "participant_info",
        'subject': "hello",
        'body': "# Foo bar\nHello"
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200).json_body

    assert participant_mail_test_results['count'] == 2 # Current user + adam

    # Assure that the crew mail count didn't increase
    crew_mail_test_post = testapp.post_json('/email/dryrun', dict({
        'recipient_category': "crew_info",
        'subject': "hello",
        'body': "# Foo bar\nHello"
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200).json_body['count']
    consenting_user_post = testapp.post_json('/email/dryrun', dict({
        'recipient_category': "event_notification",
        'subject': "hello",
        'body': "# Foo bar\nHello"
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200).json_body['count']

    assert crew_mail_test_pre == crew_mail_test_post
    assert consenting_user_pre == consenting_user_post

def test_invalid_mail_category_dryrun(testapp, upcoming_event):
    testapp.ensure_typical_event()

    # test is an admin
    sender_token, refresh = testapp.auth_get_tokens('test@example.com', 'sixcharacters')

    target_users = testapp.post_json('/email/dryrun', dict({
        'recipient_category': "swag",
        'subject': "hello",
        'body': "# Foo bar\nHello"
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=400)

def test_consent_mail_age_limit(db, testapp, upcoming_event):
    testapp.ensure_typical_event()

    # test is an admin
    sender_token, refresh = testapp.auth_get_tokens('test@example.com', 'sixcharacters')
    adam_token, refresh = testapp.auth_get_tokens('adam@example.com', 'sixcharacters')

    sender_user = testapp.get_user(sender_token)
    adam_user = testapp.get_user(adam_token)

    # Get current event, set an age limit
    current_event = testapp.get_current_event(db)
    current_event.participant_age_limit_inclusive = 300
    db.add(current_event)
    db.flush()

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


def test_last_event_participants(testapp):
    """Tests that all participants get e-mails when the participant_info category is used.
    Crew members should not receive these mails if they don't have a ticket
    
    Assumes nobody has consented to marketing mail"""
    testapp.ensure_typical_event()

    # test is an admin
    sender_token, refresh = testapp.auth_get_tokens('test@example.com', 'sixcharacters')
    adam_token, refresh = testapp.auth_get_tokens('adam@example.com', 'sixcharacters')

    sender_user = testapp.get_user(sender_token)
    adam_user = testapp.get_user(adam_token)

    participant_mail_test_results = testapp.post_json('/email/dryrun', dict({
        'recipient_category': "participant_info",
        'subject': "hello",
        'body': "# Foo bar\nHello"
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200).json_body

    assert participant_mail_test_results['count'] == 1 # Only the current user