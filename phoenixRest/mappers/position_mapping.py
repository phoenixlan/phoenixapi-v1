def map_position_mapping_with_position(position_mapping):
    return {
        'uuid': position_mapping.uuid,
        'position': position_mapping.position,
        'user_uuid': position_mapping.user_uuid,
        'event_uuid': position_mapping.event_uuid,
        'created': int(position_mapping.created.timestamp())
    }

def map_position_mapping_with_user(position_mapping):
    return {
        'uuid': position_mapping.uuid,
        'position_uuid': position_mapping.position_uuid,
        'user': position_mapping.user,
        'event_uuid': position_mapping.event_uuid,
        'created': int(position_mapping.created.timestamp())
    }