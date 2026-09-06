# Test creating applications, and that the user is qualified to do so
from wsgiref.util import application_uri

from phoenixRest.models.core.user import User
from phoenixRest.models.crew.application import Application, ApplicationState
from phoenixRest.models.crew.application_crew_mapping import ApplicationCrewMapping
from phoenixRest.models.crew.crew import Crew

from test_app import TestApp

def create_application(testapp:TestApp, token, application_crews: list, event):
    # Get the current user, ensure there is no avatar
    currentUser = testapp.get('/user/current', headers=dict({
        "Authorization": "Bearer " + token
        }), status=200).json_body

    avatar_uuid = currentUser['avatar_uuid']
    assert avatar_uuid is None

    # Upload an avatar
    testapp.post('/user/%s/avatar' % currentUser['uuid'], params="x=%d&y=%d&w=%d&h=%d"% (0, 0, 600, 450), upload_files=[('file', "phoenixRest/tests/assets/avatar_test.png")], headers=dict({
        "Authorization": "Bearer " + token
    }), status = 200)

    res = testapp.put_json('/event/%s/application' % event.uuid, dict({
        'crews': application_crews,
        'contents': 'I want to join please'
    }), headers=dict({
        "Authorization": "Bearer " + token
    }), status=200)

    application_uuid = res.json_body['uuid']
    assert application_uuid != None

    return application_uuid

def test_create_accept_appliations(testapp, upcoming_event, chief_user, adam_user, testcrew):
    # Log in as the test user
    token, refresh = testapp.auth_get_tokens(chief_user.email, 'sixcharacters')
    applicant_token, refresh = testapp.auth_get_tokens(adam_user.email, 'sixcharacters')

    application_uuid = create_application(testapp, applicant_token, [str(testcrew.uuid)], upcoming_event)

    # Try to accept the application
    res = testapp.patch_json('/application/%s' % application_uuid, dict({
        'answer': 'That\'s a very poggers application',
        'crew_uuid': str(testcrew.uuid),
        'state': 'accepted'
    }), headers=dict({
        "Authorization": "Bearer " + token
    }), status=200)

    res = testapp.get('/application/%s' % application_uuid, headers=dict({
        "Authorization": "Bearer " + token
    }), status=200)

    assert len(res.json_body) > 0
    assert res.json_body['state'] == "ApplicationState.accepted"

    # Get the user object, ensure we are now a member
    applicant_user = testapp.get('/user/current', headers=dict({
        "Authorization": "Bearer " + applicant_token
        }), status=200).json_body
    
    assert len(applicant_user['position_mappings']) > 0

    correct_mappings = list(filter(lambda mapping: mapping['event_uuid'] == str(upcoming_event.uuid), applicant_user['position_mappings']))
    assert len(correct_mappings) == 1
    assert correct_mappings[0]['position']['crew_uuid'] == str(testcrew.uuid)
    assert correct_mappings[0]['position']['event_brand_uuid'] == \
        str(upcoming_event.event_brand_uuid)

    # A newly generated token validates the event/position brand pairing.
    testapp.auth_get_tokens(adam_user.email, 'sixcharacters')
    
def test_create_reject_appliations(testapp, upcoming_event, admin_user, greg_user, testcrew):
    # Log in as the test user
    token, refresh = testapp.auth_get_tokens(admin_user.email, 'sixcharacters')
    applicant_token, refresh = testapp.auth_get_tokens(greg_user.email, 'sixcharacters')

    application_crew = str(testcrew.uuid)

    application_uuid = create_application(testapp, applicant_token, [application_crew], upcoming_event)

    # Try to accept the application
    res = testapp.patch_json('/application/%s' % application_uuid, dict({
        'answer': 'Nah man',
        'state': 'rejected'
    }), headers=dict({
        "Authorization": "Bearer " + token
    }), status=200)

    res = testapp.get('/application/%s' % application_uuid, headers=dict({
        "Authorization": "Bearer " + token
    }), status=200)

    assert len(res.json_body) > 0
    assert res.json_body['state'] == "ApplicationState.rejected"

    # Ensure the member didn't join any crews
    applicant_user = testapp.get('/user/current', headers=dict({
        "Authorization": "Bearer " + applicant_token
        }), status=200).json_body
    
    assert len(applicant_user['position_mappings']) > 0

    correct_mappings = list(filter(lambda mapping: mapping['event_uuid'] == str(upcoming_event.uuid), applicant_user['position_mappings']))
    assert len(correct_mappings) == 0
    
def hide_application(testapp, token, application_crews: list, upcoming_event, admin_user, greg_user):
    token, refresh = testapp.auth_get_tokens(admin_user.email, 'sixcharacters')
    applicant_token, refresh = testapp.auth_get_tokens(greg_user.email, 'sixcharacters')

    user = testapp.get_user(token)

    my_application_list = testapp.get('/application/my' % application_uuid, headers=dict({
        "Authorization": "Bearer " + applicant_token
    }), status=200).json_body

    assert len(my_application_list) == 0

    application_uuid = create_application(testapp, applicant_token, application_crews, upcoming_event)

    my_application_list = testapp.get('/application/my', headers=dict({
        "Authorization": "Bearer " + applicant_token
    }), status=200).json_body

    assert len(my_application_list) == 1

    # Check that you can get applications through user uuid
    my_application_list = testapp.get('/user/%s/applications' % user['uuid'], headers=dict({
        "Authorization": "Bearer " + applicant_token
    }), status=200).json_body

    assert len(my_application_list) == 1

    # Try to hide the application
    res = testapp.patch_json('/application/%s/hide' % application_uuid, headers=dict({
        "Authorization": "Bearer " + token
    }), status=200)

    # It should be gone
    res = testapp.get('/application/%s' % application_uuid, headers=dict({
        "Authorization": "Bearer " + applicant_token
    }), status=404)

    my_application_list = testapp.get('/application/my' % application_uuid, headers=dict({
        "Authorization": "Bearer " + applicant_token
    }), status=200).json_body

    assert len(my_application_list) == 0

def test_cannot_create_application_noncurrent_event(testapp, db, previous_event, greg_user, testcrew):
    # Log in as applicant
    applicant_token, refresh = testapp.auth_get_tokens(greg_user.email, 'sixcharacters')

    # Get the current user and upload an avatar (required for applications)
    currentUser = testapp.get('/user/current', headers=dict({
        "Authorization": "Bearer " + applicant_token
    }), status=200).json_body

    testapp.post('/user/%s/avatar' % currentUser['uuid'], params="x=%d&y=%d&w=%d&h=%d"% (0, 0, 600, 450), upload_files=[('file', "phoenixRest/tests/assets/avatar_test.png")], headers=dict({
        "Authorization": "Bearer " + applicant_token
    }), status = 200)

    # Get applyable crews
    application_crew_candidates = list(filter(lambda crew: crew["is_applyable"], testapp.get('/crew', status=200).json_body))

    # Attempt to create an application for the past event - should fail
    res = testapp.put_json('/event/%s/application' % previous_event.uuid, dict({
        'crews': [str(testcrew.uuid)],
        'contents': 'I want to join please'
    }), headers=dict({
        "Authorization": "Bearer " + applicant_token
    }), status=400)

    assert res.json_body['error'] == "Event is not current - you can't create an application for a non-current event"

def test_application_rejects_crew_from_other_brand(
        testapp, upcoming_event, greg_user, other_crew):
    token, refresh = testapp.auth_get_tokens(greg_user.email, 'sixcharacters')
    testapp.upload_avatar(
        token, 'phoenixRest/tests/assets/avatar_test.png',
        0, 0, 600, 450, expected_status=200
    )

    response = testapp.put_json(
        '/event/%s/application' % upcoming_event.uuid,
        {
            'crews': [str(other_crew.uuid)],
            'contents': 'Cross-brand application'
        },
        headers={'Authorization': "Bearer " + token},
        status=400
    )

    assert response.json_body['error'] == \
        'Crew belongs to a different event brand'
