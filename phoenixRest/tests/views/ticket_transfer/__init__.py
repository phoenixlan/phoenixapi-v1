from phoenixRest.models.tickets.ticket_transfer import TicketTransfer

from datetime import datetime, timedelta

import pyotp

def test_ticket_transfer_flow(testapp, upcoming_event, ticket_types, admin_user, jeff_user, adam_user):
    # test is an admin
    sender_token, refresh = testapp.auth_get_tokens(admin_user.email, 'sixcharacters')
    receiver_token, refresh = testapp.auth_get_tokens(jeff_user.email, 'sixcharacters')
    receiver_2_token , refresh = testapp.auth_get_tokens(adam_user.email, 'sixcharacters')

    # Get user UUID
    sender_user = testapp.get_user(sender_token)
    receiver_user = testapp.get_user(receiver_token)
    receiver_2_user = testapp.get_user(receiver_2_token)

    # Get existing ticket types
    res = testapp.get('/event/%s/ticketType' % upcoming_event.uuid, headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200)
    ticket_type = res.json_body[0]

    # Give test a free ticket. Only works because test is an admin
    res = testapp.post_json('/event/%s/ticket' % upcoming_event.uuid, dict({
        'ticket_type': ticket_type['uuid'],
        'recipient': sender_user['uuid']
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200)

    # List the tickets owned by the test user
    owned_tickets = testapp.get('/user/%s/owned_tickets' % sender_user['uuid'], headers=dict({
        "Authorization": "Bearer " + sender_token 
    }), status=200).json_body
    assert len(owned_tickets) > 0

    # Get the tickets owned by the recipient prior to transfer
    owned_tickets_recipient = testapp.get('/user/%s/owned_tickets' % receiver_user['uuid'], headers=dict({
        "Authorization": "Bearer " + receiver_token
    }), status=200).json_body

    transfer_ticket = owned_tickets[0]

    # Someone who doesn't own a ticket can't transfer it
    res = testapp.post_json('/ticket/%s/transfer' % transfer_ticket['ticket_id'], dict({
        'user_email': receiver_user['email']
    }), headers=dict({
        "Authorization": "Bearer " + receiver_token
    }), status=403)

    # Transfer a ticket
    res = testapp.post_json('/ticket/%s/transfer' % transfer_ticket['ticket_id'], dict({
        'user_email': receiver_user['email']
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200)

    # Verify that the owner changed
    transferred_ticket = testapp.get('/ticket/%s' % transfer_ticket['ticket_id'], headers=dict({
        "Authorization": "Bearer " + receiver_token
    }), status=200).json_body
    assert transferred_ticket['owner']['uuid'] == receiver_user['uuid']

    # Verify that a ticket disappeared
    owned_tickets_post_transfer = testapp.get('/user/%s/owned_tickets' % sender_user['uuid'], headers=dict({
        "Authorization": "Bearer " + sender_token 
    }), status=200).json_body
    assert len(owned_tickets_post_transfer) < len(owned_tickets)

    # Check that the recipient received a ticket
    owned_tickets_recipient_post_transfer = testapp.get('/user/%s/owned_tickets' % receiver_user['uuid'], headers=dict({
        "Authorization": "Bearer " + receiver_token
    }), status=200).json_body

    assert len(owned_tickets_recipient_post_transfer) > len(owned_tickets_recipient)

    # Check that both people can see the ticket transfer, and assert it is not reversed and not expired
    sender_transfers = testapp.get('/user/%s/ticket_transfers?event_uuid=%s' % (sender_user['uuid'], upcoming_event.uuid), headers=dict({
        "Authorization": "Bearer " + sender_token,
    }), status=200).json_body

    assert len(sender_transfers) == 1

    receiver_transfers = testapp.get('/user/%s/ticket_transfers?event_uuid=%s' % (receiver_user['uuid'], upcoming_event.uuid), headers=dict({
        "Authorization": "Bearer " + receiver_token,
    }), status=200).json_body

    assert len(receiver_transfers) == 1

    assert receiver_transfers[0]['uuid'] == sender_transfers[0]['uuid']

    assert not sender_transfers[0]['expired']
    assert not sender_transfers[0]['reverted']

    # The receiver can't revert
    testapp.post_json('/ticket_transfer/%s/revert' % receiver_transfers[0]['uuid'], dict({
    }), headers=dict({
        "Authorization": "Bearer " + receiver_token
    }), status=403)

    # The receiver can't send the transfer to a third person
    res = testapp.post_json('/ticket/%s/transfer' % transfer_ticket['ticket_id'], dict({
        'user_email': receiver_2_user['email']
    }), headers=dict({
        "Authorization": "Bearer " + receiver_token
    }), status=400)

    # Revert the ticket transfer
    testapp.post_json('/ticket_transfer/%s/revert' % receiver_transfers[0]['uuid'], dict({
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200)

    # Check that the transfer isn't gone
    sender_transfers = testapp.get('/user/%s/ticket_transfers?event_uuid=%s' % (sender_user['uuid'], upcoming_event.uuid), headers=dict({
        "Authorization": "Bearer " + sender_token,
    }), status=200).json_body

    assert len(sender_transfers) == 1

    receiver_transfers = testapp.get('/user/%s/ticket_transfers?event_uuid=%s' % (receiver_user['uuid'], upcoming_event.uuid), headers=dict({
        "Authorization": "Bearer " + receiver_token,
    }), status=200).json_body

    assert len(receiver_transfers) == 1

    assert sender_transfers[0]['reverted']
    assert receiver_transfers[0]['reverted']

    # Make sure the owner has chagned back
    transferred_ticket = testapp.get('/ticket/%s' % transfer_ticket['ticket_id'], headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200).json_body
    assert transferred_ticket['owner']['uuid'] == sender_user['uuid']

    # You cannot revert something that is already reverted
    testapp.post_json('/ticket_transfer/%s/revert' % receiver_transfers[0]['uuid'], dict({
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=400)

def test_non_transferable_ticket_cannot_be_transferred(testapp, upcoming_event, jeff_user, adam_user, jeff_non_transferable_ticket):
    token, refresh = testapp.auth_get_tokens(jeff_user.email, 'sixcharacters')

    # The owner can't transfer a ticket whose ticket type is not transferable
    testapp.post_json('/ticket/%s/transfer' % jeff_non_transferable_ticket.ticket_id, dict({
        'user_email': adam_user.email
    }), headers=dict({
        "Authorization": "Bearer " + token
    }), status=400)

    # The owner is unchanged
    ticket = testapp.get('/ticket/%s' % jeff_non_transferable_ticket.ticket_id, headers=dict({
        "Authorization": "Bearer " + token
    }), status=200).json_body
    assert ticket['owner']['uuid'] == str(jeff_user.uuid)
    assert ticket['ticket_type']['transferable'] is False

    # No transfer was recorded
    transfers = testapp.get('/user/%s/ticket_transfers?event_uuid=%s' % (jeff_user.uuid, upcoming_event.uuid), headers=dict({
        "Authorization": "Bearer " + token,
    }), status=200).json_body
    assert len(transfers) == 0

def test_checked_in_ticket_cannot_be_transferred(testapp, db, upcoming_event, jeff_user, adam_user, jeff_membership_ticket):
    jeff_membership_ticket.checked_in = datetime.now()
    db.flush()

    token, refresh = testapp.auth_get_tokens(jeff_user.email, 'sixcharacters')

    # The owner can't transfer a ticket that has already been checked in
    testapp.post_json('/ticket/%s/transfer' % jeff_membership_ticket.ticket_id, dict({
        'user_email': adam_user.email
    }), headers=dict({
        "Authorization": "Bearer " + token
    }), status=400)

    # The owner is unchanged
    ticket = testapp.get('/ticket/%s' % jeff_membership_ticket.ticket_id, headers=dict({
        "Authorization": "Bearer " + token
    }), status=200).json_body
    assert ticket['owner']['uuid'] == str(jeff_user.uuid)
    assert ticket['checked_in'] is not None

    # No transfer was recorded
    transfers = testapp.get('/user/%s/ticket_transfers?event_uuid=%s' % (jeff_user.uuid, upcoming_event.uuid), headers=dict({
        "Authorization": "Bearer " + token,
    }), status=200).json_body
    assert len(transfers) == 0

def test_ticket_cannot_be_transferred_to_yourself(testapp, upcoming_event, jeff_user, jeff_membership_ticket):
    token, refresh = testapp.auth_get_tokens(jeff_user.email, 'sixcharacters')

    # The owner can't transfer a ticket to themselves
    testapp.post_json('/ticket/%s/transfer' % jeff_membership_ticket.ticket_id, dict({
        'user_email': jeff_user.email
    }), headers=dict({
        "Authorization": "Bearer " + token
    }), status=400)

    # No transfer was recorded
    transfers = testapp.get('/user/%s/ticket_transfers?event_uuid=%s' % (jeff_user.uuid, upcoming_event.uuid), headers=dict({
        "Authorization": "Bearer " + token,
    }), status=200).json_body
    assert len(transfers) == 0

def test_expired_transfer_cannot_be_reverted(testapp, db, jeff_user, adam_user, jeff_membership_ticket):
    token, refresh = testapp.auth_get_tokens(jeff_user.email, 'sixcharacters')

    transfer = testapp.post_json('/ticket/%s/transfer' % jeff_membership_ticket.ticket_id, dict({
        'user_email': adam_user.email
    }), headers=dict({
        "Authorization": "Bearer " + token
    }), status=200).json_body

    # Move the transfer back in time so it is past the revert window
    transfer_model = db.query(TicketTransfer).filter(TicketTransfer.uuid == transfer['uuid']).one()
    expiry = int(testapp.app.registry.settings['ticket.transfer.expiry'])
    transfer_model.created = datetime.now() - timedelta(seconds=expiry + 60)
    db.flush()

    testapp.post_json('/ticket_transfer/%s/revert' % transfer['uuid'], dict({
    }), headers=dict({
        "Authorization": "Bearer " + token
    }), status=400)

    assert jeff_membership_ticket.owner == adam_user
    assert not transfer_model.reverted

def test_checked_in_transfer_cannot_be_reverted(testapp, db, jeff_user, adam_user, jeff_membership_ticket):
    token, refresh = testapp.auth_get_tokens(jeff_user.email, 'sixcharacters')

    transfer = testapp.post_json('/ticket/%s/transfer' % jeff_membership_ticket.ticket_id, dict({
        'user_email': adam_user.email
    }), headers=dict({
        "Authorization": "Bearer " + token
    }), status=200).json_body

    # The recipient has already used the ticket
    jeff_membership_ticket.checked_in = datetime.now()
    db.flush()

    testapp.post_json('/ticket_transfer/%s/revert' % transfer['uuid'], dict({
    }), headers=dict({
        "Authorization": "Bearer " + token
    }), status=400)

    assert jeff_membership_ticket.owner == adam_user

def test_revert_invalidates_recipient_totp(testapp, jeff_user, adam_user, jeff_membership_ticket):
    sender_token, refresh = testapp.auth_get_tokens(jeff_user.email, 'sixcharacters')
    receiver_token, refresh = testapp.auth_get_tokens(adam_user.email, 'sixcharacters')

    transfer = testapp.post_json('/ticket/%s/transfer' % jeff_membership_ticket.ticket_id, dict({
        'user_email': adam_user.email
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200).json_body

    # The recipient generates a QR code for the ticket
    totp_secret = testapp.get('/ticket/%s/totp' % jeff_membership_ticket.ticket_id, headers=dict({
        "Authorization": "Bearer " + receiver_token
    }), status=200).json_body['totp']
    recipient_code = pyotp.TOTP(totp_secret, digits=8).now()

    testapp.post_json('/ticket_transfer/%s/revert' % transfer['uuid'], dict({
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200)

    # The recipient's QR code no longer verifies the ticket
    testapp.get('/ticket/%s?totp=%s' % (jeff_membership_ticket.ticket_id, recipient_code), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=403)

def test_revert_resets_seater(testapp, jeff_user, adam_user, jeff_membership_ticket):
    sender_token, refresh = testapp.auth_get_tokens(jeff_user.email, 'sixcharacters')
    receiver_token, refresh = testapp.auth_get_tokens(adam_user.email, 'sixcharacters')

    transfer = testapp.post_json('/ticket/%s/transfer' % jeff_membership_ticket.ticket_id, dict({
        'user_email': adam_user.email
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200).json_body

    # The recipient makes themselves the seater
    ticket = testapp.put_json('/ticket/%s/seater' % jeff_membership_ticket.ticket_id, dict({
    }), headers=dict({
        "Authorization": "Bearer " + receiver_token
    }), status=200).json_body
    assert ticket['seater']['uuid'] == str(adam_user.uuid)

    testapp.post_json('/ticket_transfer/%s/revert' % transfer['uuid'], dict({
    }), headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200)

    ticket = testapp.get('/ticket/%s' % jeff_membership_ticket.ticket_id, headers=dict({
        "Authorization": "Bearer " + sender_token
    }), status=200).json_body
    assert ticket['owner']['uuid'] == str(jeff_user.uuid)
    assert ticket['seater']['uuid'] == str(jeff_user.uuid)
