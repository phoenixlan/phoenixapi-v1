def test_event_brand_ticket_type_listing_as_ticket_audit(testapp, upcoming_event, ticket_types, ticket_audit_user):
    """Test that you can list ticket types for an event brand with ticket audit permission"""
    privileged_token, refresh = testapp.auth_get_tokens(ticket_audit_user.email, 'sixcharacters')

    # Test ACL functionality for TICKET_AUDIT, check that that the permission 'get_all_ticket_types' works.
    # The user should be able to read the ticket type list, we expect status code 200, and a list of the ticket types.
    res = testapp.get('/event_brand/%s/ticket_type' % upcoming_event.event_brand_uuid, headers=dict({
        "Authorization": "Bearer " + privileged_token
    }), status=200)
    assert len(res.json_body) > 0