def map_event_simple(event):
    return {
        'uuid': str(event.uuid),
        'participant_age_limit_inclusive': event.participant_age_limit_inclusive,
        'crew_age_limit_inclusive': event.crew_age_limit_inclusive,
        'booking_time': int(event.booking_time.timestamp()),
        'priority_seating_time_delta': event.priority_seating_time_delta,
        'seating_time_delta': event.seating_time_delta,
        'start_time': int(event.start_time.timestamp()),
        'end_time': int(event.end_time.timestamp()),
        'theme': event.theme,
        'max_participants': event.max_participants,
        'cancellation_reason': event.cancellation_reason,
        'seatmap_uuid': event.seatmap_uuid
    }