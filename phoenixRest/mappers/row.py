from phoenixRest.mappers.seat import map_seat_for_availability

def map_row_for_availability(row):
    return {
        'uuid': str(row.uuid),
        'x': row.x,
        'y': row.y,
        'is_horizontal': row.is_horizontal,
        'entrance': row.entrance,
        'ticket_type_uuid': row.ticket_type_uuid,
        'row_number': row.row_number,
        'seats': [ map_seat_for_availability(seat) for seat in row.seats ]
    }