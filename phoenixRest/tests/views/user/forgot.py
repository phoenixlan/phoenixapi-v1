from phoenixRest.models.core.user import User
from phoenixRest.models.core.password_reset_code import PasswordResetCode


def reset_codes_for(db, email):
    """Returns all password reset codes belonging to the user with the given e-mail"""
    user = db.query(User).filter(User.email == email.lower()).first()
    assert user is not None
    return db.query(PasswordResetCode).filter(PasswordResetCode.user_uuid == user.uuid).all()


def test_forgot_password_creates_reset_code(testapp, db, jeff_user):
    """A forgot password request for an existing user creates a reset code for that user"""
    # The user shouldn't have any reset codes to begin with
    assert len(reset_codes_for(db, jeff_user.email)) == 0

    testapp.post_json('/user/forgot', dict({
        "login": jeff_user.email,
        "client_id": "phoenix-crew-test"
    }), status=200)

    # A single reset code should now exist, tied to the requested client
    codes = reset_codes_for(db, jeff_user.email)
    assert len(codes) == 1
    assert codes[0].client_id == "phoenix-crew-test"
    assert len(codes[0].code) > 0


def test_forgot_password_normalizes_login(testapp, db, jeff_user):
    """The login is lowercased and stripped, so surrounding whitespace and casing still match a user"""
    testapp.post_json('/user/forgot', dict({
        "login": "  %s  " % jeff_user.email.upper(),
        "client_id": "phoenix-crew-test"
    }), status=200)

    codes = reset_codes_for(db, jeff_user.email)
    assert len(codes) == 1


def test_forgot_password_unknown_user_is_silent(testapp, db):
    """A request for an account that doesn't exist still returns 200, to avoid leaking which
    e-mail addresses are registered, and creates no reset code"""
    before = db.query(PasswordResetCode).count()

    testapp.post_json('/user/forgot', dict({
        "login": "doesnotexist@example.com",
        "client_id": "phoenix-crew-test"
    }), status=200)

    # No reset code should have been created for the nonexistent account
    assert db.query(PasswordResetCode).count() == before


def test_forgot_password_invalid_client_id(testapp, db, jeff_user):
    """An unknown OAuth client ID is rejected, and no reset code is created even for a real user"""
    result = testapp.post_json('/user/forgot', dict({
        "login": jeff_user.email,
        "client_id": "foo-bar-baz"
    }), status=400).json_body
    assert result["error"] == "Invalid OAuth client ID"

    assert len(reset_codes_for(db, jeff_user.email)) == 0


def test_forgot_password_validation(testapp, jeff_user):
    """Both login and client_id are required fields"""
    for key in ["login", "client_id"]:
        request_obj = dict({
            "login": jeff_user.email,
            "client_id": "phoenix-crew-test"
        })
        del request_obj[key]

        missing = testapp.post_json('/user/forgot', request_obj, status=400)
        assert key in missing.text
