from phoenixRest.mappers.position import map_position_with_users

def map_crew(crew, request):
	return {
        'uuid': crew.uuid,
        'name': crew.name,
        'description': crew.description,
        'active': crew.active,
        'is_applyable': crew.is_applyable,
        'application_prompt': crew.application_prompt,
        'hex_color': crew.hex_color,
        'teams': crew.teams,
        'positions': [map_position_with_users(position, request) for position in crew.positions]
    }

def map_crew_simple(crew, request):
	return {
        'uuid': crew.uuid,
        'name': crew.name,
        'description': crew.description,
        'active': crew.active,
        'is_applyable': crew.is_applyable,
        'application_prompt': crew.application_prompt,
        'hex_color': crew.hex_color
    }