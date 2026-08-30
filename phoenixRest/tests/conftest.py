from phoenixRest.models.core.event_brand import EventBrand
from pyramid.paster import get_appsettings
import pytest
import transaction
from phoenixRest.tests.test_app import TestApp
from phoenixRest.models import setup_dbengine, get_tm_session
from phoenixRest.models.core.event import Event
from phoenixRest.models.core.user import Gender, User
from phoenixRest.models.crew.crew import Crew
from phoenixRest.models.crew.position import Position
from phoenixRest.models.crew.position_mapping import PositionMapping
from phoenixRest.models.crew.permission import Permission
from phoenixRest.models.crew.team import Team
from phoenixRest.models.tickets.ticket_type import TicketType
from phoenixRest import main

from datetime import date, datetime, timedelta

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
def event_brand(db):
    """Creates an event brand that an event can be associated with"""
    brand = EventBrand("Event brand!")
    db.add(brand)
    db.flush()
    return brand

@pytest.fixture
def other_event_brand(db):
    brand = EventBrand("Other event brand")
    db.add(brand)
    db.flush()
    return brand

@pytest.fixture
def other_crew(db, other_event_brand):
    crew = Crew('Other crew', 'Crew belonging to another event brand')
    crew.event_brand = other_event_brand
    db.add(crew)
    db.flush()
    return crew

@pytest.fixture
def other_position(db, other_event_brand):
    position = Position('Other position', 'Position belonging to another event brand')
    position.event_brand = other_event_brand
    db.add(position)
    db.flush()
    return position

@pytest.fixture
def other_ticket_type(db, other_event_brand):
    ticket_type = TicketType(
        'Other ticket type', 100, 'Ticket type belonging to another event brand',
        True, True
    )
    ticket_type.event_brand = other_event_brand
    db.add(ticket_type)
    db.flush()
    return ticket_type

@pytest.fixture
def testcrew(db, event_brand):
    crew = Crew('Test crew', 'Crew created for tests')
    crew.event_brand = event_brand
    db.add(crew)
    db.flush()
    return crew

@pytest.fixture
def testteam(db, testcrew):
    team = Team(testcrew, 'Test team', 'Team created for tests')
    db.add(team)
    db.flush()
    return team

def _create_user(db, username, email, firstname, lastname, phone):
    user = User(
        username, email, 'sixcharacters', firstname, lastname,
        date(1998, 3, 27), Gender.male, phone, '1. Mann. Co rd', '1395'
    )
    db.add(user)
    db.flush()
    return user

def _add_crew_position(db, user, testcrew, testteam=None):
    position = Position(None, None)
    position.crew = testcrew
    position.team = testteam
    position.event_brand = testcrew.event_brand
    db.add(PositionMapping(user, position))
    db.flush()

def _create_scoped_permission_user(db, event, permission, username, email):
    user = _create_user(db, username, email, username.title(), 'User', '99999999')
    position = Position('%s position' % permission, 'Position used by tests')
    position.event_brand = event.event_brand
    db.add(Permission(position, permission, None))
    db.add(PositionMapping(user, position, event))
    db.flush()
    return user

@pytest.fixture
def admin_user(db, testcrew):
    user = _create_user(db, 'test', 'test@example.com', 'Test', 'Testesen', '98643254')
    admin_position = db.query(Position).filter(Position.name == 'Superadmin').one()
    db.add(PositionMapping(user, admin_position))
    _add_crew_position(db, user, testcrew)
    return user

@pytest.fixture
def greg_user(db, testcrew, testteam):
    user = _create_user(db, 'greg', 'greg@example.com', 'Greg', 'Gregsson', '99999999')
    _add_crew_position(db, user, testcrew, testteam)
    return user

@pytest.fixture
def jeff_user(db, testcrew, testteam):
    user = _create_user(db, 'jeff', 'jeff@example.com', 'Jeff', 'Jefferson', '99999999')
    _add_crew_position(db, user, testcrew, testteam)
    return user

@pytest.fixture
def adam_user(db):
    return _create_user(db, 'adam', 'adam@example.com', 'Adam', 'Adamson', '99999999')

@pytest.fixture
def ticket_admin_user(db, upcoming_event):
    return _create_scoped_permission_user(
        db, upcoming_event, 'ticket_admin', 'ticketadmin',
        'ticketadmin@example.com'
    )

@pytest.fixture
def hr_admin_user(db, upcoming_event):
    return _create_scoped_permission_user(
        db, upcoming_event, 'hr_admin', 'hradmin', 'hradmin@example.com'
    )

@pytest.fixture
def chief_user(db, upcoming_event, testcrew):
    user = _create_user(
        db, 'chief', 'chief@example.com', 'Chief', 'User', '99999999'
    )
    position = Position(None, None)
    position.event_brand = upcoming_event.event_brand
    position.crew = testcrew
    position.chief = True
    db.add(PositionMapping(user, position, upcoming_event))
    db.flush()
    return user

@pytest.fixture
def brand_position(db, event_brand):
    position = Position('Brand position', 'Position without a crew')
    position.event_brand = event_brand
    db.add(position)
    db.flush()
    return position

@pytest.fixture
def admin_token(testapp, admin_user):
    privileged_token, refresh = testapp.auth_get_tokens(admin_user.email, 'sixcharacters')
    return privileged_token

@pytest.fixture
def upcoming_event(db, event_brand):
    """Creates an event that has not yet happened, but where ticketsale hasn't started yet"""

    event_start = datetime.now() + timedelta(days=62)
    event_end = datetime.now() + timedelta(days=65)

    e = Event("Test event", event_start, event_end, 400, event_brand)
    db.add(e)
    db.flush()
    return e

@pytest.fixture
def other_upcoming_event(db, other_event_brand):
    event_start = datetime.now() + timedelta(days=62)
    event_end = datetime.now() + timedelta(days=65)

    event = Event(
        "Other upcoming event", event_start, event_end, 400,
        other_event_brand
    )
    db.add(event)
    db.flush()
    return event

@pytest.fixture
def ticketsale_ongoing_event(db, event_brand):
    """Creates an event that has not yet happened, where the ticket sale is currently ongoing"""

    event_start = datetime.now() + timedelta(days=10)
    event_end = datetime.now() + timedelta(days=13)

    e = Event("Test event(Ticket sale ongoing)", event_start, event_end, 400, event_brand)
    db.add(e)
    db.flush()
    return e

@pytest.fixture
def ongoing_ticket_types(db, testapp, ticketsale_ongoing_event, admin_token):
    """Adds existing ticket types to the current event (ticketsale ongoing)"""

    all_ticket_types = testapp.get('/ticketType', headers=dict({
        'Authorization': "Bearer " + admin_token
    }), status=200).json_body

    for ticket_type in all_ticket_types:
        testapp.put_json('/event/%s/ticketType' % ticketsale_ongoing_event.uuid, dict({
            'ticket_type_uuid': ticket_type['uuid']
        }), headers=dict({
            'Authorization': "Bearer " + admin_token
        }), status=200)
    
    
@pytest.fixture
def ticket_types(db, testapp, upcoming_event, admin_token):
    """Adds existing ticket types to the _upcoming event_ (sale not ongoing)"""

    all_ticket_types = testapp.get('/ticketType', headers=dict({
        'Authorization': "Bearer " + admin_token
    }), status=200).json_body

    for ticket_type in all_ticket_types:
        testapp.put_json('/event/%s/ticketType' % upcoming_event.uuid, dict({
            'ticket_type_uuid': ticket_type['uuid']
        }), headers=dict({
            'Authorization': "Bearer " + admin_token
        }), status=200)
    
    
