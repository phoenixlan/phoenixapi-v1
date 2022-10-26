from pyramid.paster import get_app
import pytest
from phoenixRest.tests.test_app import TestApp

@pytest.fixture
def testapp():
    app = get_app('paste_pytest.ini')

    return TestApp(app)