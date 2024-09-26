from .position_mapping import map_position_mapping_with_user
def map_position_with_position_mappings(position, request):
	return {
        'uuid': position.uuid,
        'name': position.name,
        'description': position.description,
        'is_vanity': position.is_vanity,

        'crew_uuid': position.crew_uuid,
        'team_uuid': position.team_uuid,
        'position_mappings': [ map_position_mapping_with_user(position_mapping) for position_mapping in position.position_mappings ],
        'chief': position.chief,
        'permissions': position.permissions

    }