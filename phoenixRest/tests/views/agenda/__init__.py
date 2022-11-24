# Test getting the current event
def test_get_agenda(testapp):
    testapp.get('/agenda/', status=200)

