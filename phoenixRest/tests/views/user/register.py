from phoenixRest.models.core.user import User
from phoenixRest.models.core.activation_code import ActivationCode

from datetime import date

def test_activate_user_by_code(testapp, db):
    """Tests that users can self-service activate themselves by e-mail link"""
    # Test that the site handles an invalid request
    fetchedUser = testapp.get('/user/activate', headers=dict({
    }), status=400)

    # Test that the site handles a code that doesn't exist
    fetchedUser = testapp.get('/user/activate?code=foobar', headers=dict({
    }), status=404)

    # Give an user a registration code
    user = db.query(User).filter(User.email == "test@example.com").first()
    assert user is not None
    # The client ID must exist in paste_pytest.ini
    user.activation_code = ActivationCode(user, "phoenix-crew-test")
    db.add(user.activation_code)
    
    resp = testapp.get(f'/user/activate?code={user.activation_code.code}', headers=dict({
    }), status=200)

def test_smoketest_registration(testapp):
    # ensure you can register
    user_register_obj = dict({
        "username": "testfoo_123",
        "firstname": "Jeff",
        "surname": "Jefferson",
        "password": "test123",
        "passwordRepeat": "test123",
        "email": "testfoo@example.com",
        "emailRepeat": "testfoo@example.com",
        "gender": "male",
        "dateOfBirth": "1998-03-27",
        "phone": "90000000", # Fake
        "guardianPhone": "", # Over 18, so this should be allowed
        "address": "1 fake street",
        "zip": "1337",
        "event_notice_consent": True,
        "clientId": "phoenix-crew-test"
    })
    user_registration_result = testapp.post_json('/user/register', user_register_obj, status=200).json_body
    assert user_registration_result['message'] == "An e-mail has been sent"

def test_register_validation(testapp):
    # Ensure we validate the registration form
    user_register_obj = dict({
        "username": "testfoo_123",
        "firstname": "Jeff",
        "surname": "Jefferson",
        "password": "test123",
        "passwordRepeat": "test123",
        "email": "testfoo@example.com",
        "emailRepeat": "testfoo@example.com",
        "gender": "male",
        "dateOfBirth": "1998-03-27",
        "phone": "90000000", # Fake
        "guardianPhone": "", # Fake
        "address": "1 fake street",
        "zip": "1337",
        "event_notice_consent": True,
    })
    for key in user_register_obj.keys():
        new_obj = user_register_obj.copy()
        del new_obj[key]

        missing_username = testapp.post_json('/user/register', new_obj, status=400)
        assert key in missing_username.text
    
    # Does it validate that email and password must match?
    not_repeat_pw = testapp.post_json('/user/register', dict({
        **user_register_obj,
        "passwordRepeat": "foobar"
    }), status=400).json_body
    assert not_repeat_pw["error"] == "Password and repeat password does not match"

    # Email?
    not_repeat_email = testapp.post_json('/user/register', dict({
        **user_register_obj,
        "emailRepeat": "foobar"
    }), status=400).json_body
    assert not_repeat_email["error"] == "Email and repeat email does not match"

    # Does it validate the password?
    short_pw = testapp.post_json('/user/register', dict({
        **user_register_obj,
        "password": "123",
        "passwordRepeat": "123"
    }), status=400).json_body
    assert short_pw["error"] == "Password is too short. Use at least 6 characters"

    # What if the user already exists?
    existing_user = testapp.post_json('/user/register', dict({
        **user_register_obj,
        "username": "test"
    }), status=400).json_body
    assert existing_user["error"] == "A user by this username, phone number, or e-mail already exists"

    # Do we validate emails?
    email_regex = testapp.post_json('/user/register', dict({
        **user_register_obj,
        "email": "foobar",
        "emailRepeat": "foobar"
    }), status=400).json_body
    assert email_regex["error"] == "You must enter a valid e-mail address"

    # Empty username?
    empty_username = testapp.post_json('/user/register', dict({
        **user_register_obj,
        "username": ""
    }), status=400).json_body
    assert empty_username["error"] == "A username is required"

    # Empty name?
    empty_name = testapp.post_json('/user/register', dict({
        **user_register_obj,
        "firstname": ""
    }), status=400).json_body
    assert empty_name["error"] == "A name is required"
    empty_name = testapp.post_json('/user/register', dict({
        **user_register_obj,
        "surname": ""
    }), status=400).json_body
    assert empty_name["error"] == "A name is required"

    # Invalid birthdate?
    invalid_birthdate = testapp.post_json('/user/register', dict({
        **user_register_obj,
        "dateOfBirth": "foobar"
    }), status=400).json_body
    assert invalid_birthdate["error"] == "Invalid birthdate format"
    invalid_birthdate = testapp.post_json('/user/register', dict({
        **user_register_obj,
        "dateOfBirth": ""
    }), status=400).json_body
    assert invalid_birthdate["error"] == "Enter a valid birthdate"

    # Future birthdate?
    this_year = date.today().year

    future_birthdate = testapp.post_json('/user/register', dict({
        **user_register_obj,
        "dateOfBirth": f"{this_year+1}-03-27"
    }), status=400).json_body
    assert future_birthdate["error"] == "Invalid birthday - you cannot be born in the future!"

    # Gender?
    not_repeat_email = testapp.post_json('/user/register', dict({
        **user_register_obj,
        "gender": "computer"
    }), status=400).json_body
    assert not_repeat_email["error"] == "Invalid gender"

    # Guardian phone - if the user is under 18 they need their parents number
    guardian_underage = testapp.post_json('/user/register', dict({
        **user_register_obj,
        "guardianPhone": "",
        "dateOfBirth": f"{this_year-10}-03-27"
    }), status=400).json_body
    assert guardian_underage["error"] == "You need to provide a guardian phone number"

    # Oauth client ID - a valid one needs to be provided so we can redirect.
    oauth_id = testapp.post_json('/user/register', dict({
        **user_register_obj,
        "clientId": "foo-bar-baz"
    }), status=400).json_body
    assert oauth_id["error"] == "Invalid OAuth client ID"