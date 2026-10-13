def _get_new_memberships(testapp, event, user, status=200):
    token, _ = testapp.auth_get_tokens(user.email, 'sixcharacters')
    return testapp.get('/event/%s/new_memberships' % event.uuid, headers=dict({
        "Authorization": "Bearer " + token
    }), status=status)

def test_new_memberships_includes_membership_personalia(testapp, upcoming_event, admin_user, brand_admin_user, jeff_user, jeff_membership_ticket, jeff_membership_personalia):
    """Members with personalia get it returned alongside their user"""
    memberships_as_admin = _get_new_memberships(testapp, upcoming_event, admin_user).json_body
    memberships_as_brand_admin = _get_new_memberships(testapp, upcoming_event, brand_admin_user).json_body

    assert len(memberships_as_admin) == 1
    membership_as_admin = memberships_as_admin[0]
    assert membership_as_admin['uuid'] == str(jeff_user.uuid)
    assert membership_as_admin['phone'] == jeff_user.phone
    assert membership_as_admin['membership_personalia']['address'] == jeff_membership_personalia.address
    assert membership_as_admin['membership_personalia']['postal_code'] == jeff_membership_personalia.postal_code

    assert len(memberships_as_brand_admin) == 1
    membership_as_brand_admin = memberships_as_admin[0]
    assert membership_as_brand_admin['uuid'] == str(jeff_user.uuid)
    assert membership_as_brand_admin['phone'] == jeff_user.phone
    assert membership_as_brand_admin['membership_personalia']['address'] == jeff_membership_personalia.address
    assert membership_as_brand_admin['membership_personalia']['postal_code'] == jeff_membership_personalia.postal_code

def test_new_memberships_without_membership_personalia(testapp, upcoming_event, admin_user, brand_admin_user, adam_user, adam_membership_ticket):
    """Members who have not filled in personalia are still listed"""
    memberships_as_admin = _get_new_memberships(testapp, upcoming_event, admin_user).json_body
    memberships_as_brand_admin = _get_new_memberships(testapp, upcoming_event, brand_admin_user).json_body

    assert len(memberships_as_admin) == 1
    assert memberships_as_admin[0]['uuid'] == str(adam_user.uuid)
    assert memberships_as_admin[0]['membership_personalia'] is None

    assert len(memberships_as_brand_admin) == 1
    assert memberships_as_brand_admin[0]['uuid'] == str(adam_user.uuid)
    assert memberships_as_brand_admin[0]['membership_personalia'] is None

def test_new_memberships_excludes_non_membership_tickets(testapp, upcoming_event, admin_user, jeff_user, jeff_membership_ticket, greg_non_membership_ticket):
    """Only owners of tickets that grant membership are listed"""
    memberships = _get_new_memberships(testapp, upcoming_event, admin_user).json_body

    assert [ membership['uuid'] for membership in memberships ] == [ str(jeff_user.uuid) ]

def test_new_memberships_requires_permission(testapp, upcoming_event, greg_user):
    """Regular users cannot list new memberships"""
    _get_new_memberships(testapp, upcoming_event, greg_user, status=403)
