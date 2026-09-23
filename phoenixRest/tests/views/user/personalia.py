from phoenixRest.models.core.membership_personalia import MembershipPersonalia

def test_personalia_flow(testapp, db, jeff_user):
    """Test the flow from no personalia -> personalia"""
    token, _ = testapp.auth_get_tokens(jeff_user.email, "sixcharacters")

    # There should be no personalia to begin with
    testapp.get(f'/user/{jeff_user.uuid}/membership_personalia', headers=dict({
        "Authorization": "Bearer " + token
    }), status=404)

    # Now set the personalia
    testapp.put_json(f'/user/{jeff_user.uuid}/membership_personalia', dict({
        "address": "foo st.",
        "postal_code": "13",
    }), headers=dict({
        "Authorization": "Bearer " + token
    }), status=200)

    testapp.get(f'/user/{jeff_user.uuid}/membership_personalia', headers=dict({
        "Authorization": "Bearer " + token
    }), status=200)


def test_admin_access(testapp, db, jeff_user, admin_user):
    """Admins can also access an users personalia"""
    token, _ = testapp.auth_get_tokens(admin_user.email, "sixcharacters")
    jeff_token, _ = testapp.auth_get_tokens(jeff_user.email, "sixcharacters")

    # Need to set personalia first
    testapp.put_json(f'/user/{jeff_user.uuid}/membership_personalia', dict({
        "address": "foo st.",
        "postal_code": "13",
    }), headers=dict({
        "Authorization": "Bearer " + jeff_token
    }), status=200)

    testapp.get(f'/user/{jeff_user.uuid}/membership_personalia', headers=dict({
        "Authorization": "Bearer " + token
    }), status=200)

def test_nobody_access(testapp, db, jeff_user, greg_user):
    """Random other person cannot access an users personalia"""
    token, _ = testapp.auth_get_tokens(greg_user.email, "sixcharacters")

    testapp.get(f'/user/{jeff_user.uuid}/membership_personalia', headers=dict({
        "Authorization": "Bearer " + token
    }), status=403)
