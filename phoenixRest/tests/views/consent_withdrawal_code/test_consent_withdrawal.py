from phoenixRest.models.core.user import User
from phoenixRest.models.core.user_consent import UserConsent, ConsentType
from phoenixRest.models.core.consent_withdrawal_code import ConsentWithdrawalCode

def test_consent_withdrawal(testapp, db):
    testapp.ensure_typical_event()

    test_token, refresh = testapp.auth_get_tokens('test', 'sixcharacters')
    target_token, refresh = testapp.auth_get_tokens('adam', 'sixcharacters')

    test_user = testapp.get_user(test_token)
    target_user = testapp.get_user(target_token)

    # Add consent to marketing mail to our test user
    test_user_obj = db.query(User).filter(User.uuid == target_user['uuid']).first()
    consent = UserConsent(test_user_obj, ConsentType.event_notification, "test")
    db.add(consent)
    db.flush()

    # Ensure no consent withdrawal codes exist at the moment
    code_count = db.query(ConsentWithdrawalCode).count()
    assert code_count == 0

    # Ensure a consent code is made
    # Slight overlap with the email function
    consenting_user_result = testapp.post_json('/email/dryrun', dict({
        'recipient_category': "event_notification",
        'subject': "hello",
        'body': "# Foo bar\nHello"
    }), headers=dict({
        'X-Phoenix-Auth': test_token
    }), status=200).json_body

    codes = db.query(ConsentWithdrawalCode).all()
    assert len(codes) == 1
    code = codes[0]

    # Ensure you can fetch info about the withdrawal code
    consenting_user_result = testapp.get('/consent_withdrawal_code/%s' % code.uuid, headers=dict({
        'X-Phoenix-Auth': test_token
    }), status=200).json_body

    # Try to withdraw the consent
    consenting_user_result = testapp.post_json('/consent_withdrawal_code/%s/use' % code.uuid, dict({
        'recipient_category': "event_notification",
        'subject': "hello",
        'body': "# Foo bar\nHello"
    }), status=200).json_body

    # Is the code gone?
    consenting_user_result = testapp.get('/consent_withdrawal_code/%s' % code.uuid, status=404)

    # Check that the consent is also gone
    consent_count = db.query(UserConsent).count()
    assert consent_count == 0