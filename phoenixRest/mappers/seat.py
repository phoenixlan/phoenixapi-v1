from phoenixRest.mappers.ticket import map_ticket_simple

def map_seat_for_availability(seat, request):
    return {
        'uuid': str(seat.uuid),
        'number': seat.number,
        'is_reserved': seat.is_reserved,
        'taken': seat.ticket is not None,
        'ticket_id': seat.ticket.ticket_id if seat.ticket and (seat.ticket.owner.uuid == request.user.uuid or (seat.ticket.seater is not None and seat.ticket.seater.uuid == request.user.uuid)) else None
    }

def map_seat_for_ticket(seat):
    return {
        'uuid': str(seat.uuid),
        'number': seat.number,
        'row': { # Avoid circular import dependency by just writing the mapping inline
            'uuid': str(seat.row.uuid),
            'row_number': seat.row.row_number,
            'entrance': seat.row.entrance,
        },
        'is_reserved': seat.is_reserved
    }