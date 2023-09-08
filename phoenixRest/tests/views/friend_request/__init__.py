from test_app import TestApp

def test_friend_request(testapp:TestApp):
    
    # Log in as the test user
    greg_user_token, refresh = testapp.auth_get_tokens('greg', 'sixcharacters')
    jeff_user_token, refresh = testapp.auth_get_tokens('jeff', 'sixcharacters')
    
    greg = testapp.get_user(greg_user_token)
    jeff = testapp.get_user(jeff_user_token)
    
    # Greg sends a friend request to jeff
    res = testapp.post_json('/friend_request', dict({
        "user_email":"jeff@example.com"
    }), headers=dict({
        'X-Phoenix-Auth': greg_user_token
    }), status=200)

    friend_request_uuid = res.json_body["uuid"]
    
    assert friend_request_uuid != None
    
    # Greg views all friend requests
    res = testapp.get(f'/user/{greg["uuid"]}/friendships', headers=dict({
        'X-Phoenix-Auth': greg_user_token
    }), status=200).json_body
    assert len(res) == 1
    
    # Greg tries to accept the friend request, but fails
    res = testapp.post(f'/friend_request/{friend_request_uuid}/accept', headers=dict({
        'X-Phoenix-Auth': greg_user_token
    }), status=403)
    
    # Greg views all friend requests
    res = testapp.get(f'/user/{greg["uuid"]}/friendships', headers=dict({
        'X-Phoenix-Auth': greg_user_token
    }), status=200).json_body
    assert len(res) == 1
    
    # Greg views the status of the friend request
    res = testapp.get(f'/friend_request/{friend_request_uuid}', headers=dict({
        'X-Phoenix-Auth': greg_user_token
    }), status=200)
    
    # Jeff accepts the friend request
    res = testapp.post(f'/friend_request/{friend_request_uuid}/accept', headers=dict({
        'X-Phoenix-Auth': jeff_user_token
    }), status=200)
    
    # Greg has a sudden change of heart and decides to delete the friendship
    res = testapp.delete(f'/friend_request/{friend_request_uuid}', headers=dict({
        'X-Phoenix-Auth': greg_user_token
    }), status=200)
    
    # Greg views all friendships
    res = testapp.get(f'/user/{greg["uuid"]}/friendships', headers=dict({
        'X-Phoenix-Auth': greg_user_token
    }), status=200).json_body
    assert len(res) == 0
       
    #? We try the oposite scenario where jeff deletes the friendship
    
    # Greg sends a friend request to jeff
    res = testapp.post_json('/friend_request', dict({
        "user_email":"jeff@example.com"
    }), headers=dict({
        'X-Phoenix-Auth': greg_user_token
    }), status=200)

    friend_request_uuid = res.json_body["uuid"]
    
    assert friend_request_uuid != None
    
    # Jeff accepts the friend request
    res = testapp.post(f'/friend_request/{friend_request_uuid}/accept', headers=dict({
        'X-Phoenix-Auth': jeff_user_token
    }), status=200)
    
    # Jeff has a sudden change of heart and decides to revoke the friendship
    res = testapp.delete(f'/friend_request/{friend_request_uuid}', headers=dict({
        'X-Phoenix-Auth': jeff_user_token
    }), status=200)
    
    # Greg views all friendships
    res = testapp.get(f'/user/{greg["uuid"]}/friendships', headers=dict({
        'X-Phoenix-Auth': greg_user_token
    }), status=200).json_body
    assert len(res) == 1
    
    # Jeff views all friendships
    res = testapp.get(f'/user/{jeff["uuid"]}/friendships', headers=dict({
        'X-Phoenix-Auth': jeff_user_token
    }), status=200).json_body
    assert len(res) == 0
    