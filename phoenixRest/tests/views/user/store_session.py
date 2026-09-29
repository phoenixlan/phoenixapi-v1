from phoenixRest.models.tickets.store_session import StoreSession

from datetime import datetime, timedelta

def test_get_own_store_session(testapp, db, upcoming_event, jeff_user, adam_user):
    # Jeff has a stale store session that must not be returned to Adam
    stale_session = StoreSession(jeff_user, -3600, upcoming_event)
    stale_session.created = datetime.now() - timedelta(hours=2)
    own_session = StoreSession(adam_user, 3600, upcoming_event)
    db.add_all([stale_session, own_session])
    db.flush()

    token, refresh = testapp.auth_get_tokens(adam_user.email, 'sixcharacters')
    session = testapp.get('/user/%s/store_session' % adam_user.uuid, headers=dict({
        "Authorization": "Bearer " + token
    }), status=200).json_body

    assert session['uuid'] == str(own_session.uuid)
    assert session['user_uuid'] == str(adam_user.uuid)

def test_get_store_session_ignores_other_users_stale_session(testapp, db, upcoming_event, jeff_user, adam_user):
    stale_session = StoreSession(jeff_user, -3600, upcoming_event)
    stale_session.created = datetime.now() - timedelta(hours=2)
    db.add(stale_session)
    db.flush()

    # Adam has no store session, so he must not get Jeff's
    token, refresh = testapp.auth_get_tokens(adam_user.email, 'sixcharacters')
    testapp.get('/user/%s/store_session' % adam_user.uuid, headers=dict({
        "Authorization": "Bearer " + token
    }), status=404)

def test_get_expired_own_store_session(testapp, db, upcoming_event, adam_user):
    db.add(StoreSession(adam_user, -3600, upcoming_event))
    db.flush()

    token, refresh = testapp.auth_get_tokens(adam_user.email, 'sixcharacters')
    testapp.get('/user/%s/store_session' % adam_user.uuid, headers=dict({
        "Authorization": "Bearer " + token
    }), status=404)
