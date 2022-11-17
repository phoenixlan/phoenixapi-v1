from pyramid.paster import get_appsettings
import pytest
from phoenixRest.tests.test_app import TestApp
from phoenixRest.models import setup_dbengine
from phoenixRest import main

@pytest.fixture
def dbengine():
    engine = setup_dbengine()

@pytest.fixture
def testapp(dbengine):
    app = main({}, dbengine, **get_appsettings('paste_pytest.ini'))

    return TestApp(app)

