from .event import map_event_simple

def map_ticket_simple(ticket):
    return {
        'ticket_id': ticket.ticket_id,
        'buyer_uuid': ticket.buyer_uuid,
        'owner_uuid': ticket.owner_uuid,
        'seater_uuid': ticket.seater_uuid,
        'event_uuid': ticket.event_uuid,

        'payment_uuid': ticket.payment_uuid,
        'ticket_type': ticket.ticket_type,

        'seat': ticket.seat_uuid,

        'created': int(ticket.created.timestamp())
    }