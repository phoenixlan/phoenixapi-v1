from phoenixRest.models.core.audit_log import AuditLog


def test_audit_log_is_written(testapp, db, admin_user, jeff_user):
    token, refresh = testapp.auth_get_tokens(admin_user.email, 'sixcharacters')
    headers = {"Authorization": "Bearer " + token}

    testapp.get('/user/%s' % jeff_user.uuid, headers=headers, status=200)
    testapp.get('/user/search', params={'query': jeff_user.email}, headers=headers, status=200)

    actions = [log.action for log in db.query(AuditLog).filter(AuditLog.user_uuid == admin_user.uuid)]
    assert sorted(actions) == ["user_get", "user_search"]
