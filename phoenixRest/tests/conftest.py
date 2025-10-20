from pyramid.paster import get_appsettings
import pytest
import transaction
from phoenixRest.tests.test_app import TestApp
from phoenixRest.models import setup_dbengine, get_tm_session
from phoenixRest.models.core.event import Event
from phoenixRest import main

from datetime import datetime, timedelta

import logging
log = logging.getLogger(__name__)

@pytest.fixture(scope='session')
def dbengine():
    engine = setup_dbengine()
    return engine

@pytest.fixture
def tm():
    tm = transaction.TransactionManager(explicit=True)
    tm.begin()
    tm.doom()

    yield tm

    tm.abort()

@pytest.fixture
def db(app, tm):
    log.info("Setting up db session")
    session_factory = app.registry['dbsession_factory']
    return get_tm_session(session_factory, tm)

@pytest.fixture
def app(dbengine):
    return main({}, dbengine=dbengine, **get_appsettings('paste_pytest.ini'))

@pytest.fixture()
def testapp(app, tm, db):

    return TestApp(app, extra_environ={
        'tm.active': True,
        'tm.manager': tm,
        'app.dbsession': db,
    })

@pytest.fixture
def upcoming_event(db):
    """Creates an event that has not yet happened, but where ticketsale hasn't started yet"""

    event_start = datetime.now() + timedelta(days=62)
    event_end = datetime.now() + timedelta(days=65)

    e = Event("Test event", event_start, event_end, 400)
    db.add(e)
    db.flush()
    return e

@pytest.fixture
def ticketsale_ongoing_event(db):
    """Creates an event that has not yet happened, where the ticket sale is currently ongoing"""

    event_start = datetime.now() + timedelta(days=10)
    event_end = datetime.now() + timedelta(days=13)

    e = Event("Test event(Ticket sale ongoing)", event_start, event_end, 400)
    db.add(e)
    db.flush()
    return e