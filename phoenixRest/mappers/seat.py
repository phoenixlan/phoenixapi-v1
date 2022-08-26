def map_seat_for_availability(seat):
    return {
        'uuid': str(seat.uuid),
        'number': seat.number,
        'is_reserved': seat.is_reserved,
        'taken': seat.ticket is not None
    }