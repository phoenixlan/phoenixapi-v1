from phoenixRest.mappers.position import map_position_no_crew

def map_crew(crew, request):
	return {
        'uuid': crew.uuid,
        'name': crew.name,
        'description': crew.description,
        'active': crew.active,
        'is_applyable': crew.is_applyable,
        'hex_color': crew.hex_color,
        'teams': crew.teams,
        'positions': [map_position_no_crew(position, request) for position in crew.positions]
    }

def map_crew_simple(crew, request):
	return {
        'uuid': crew.uuid,
        'name': crew.name,
        'description': crew.description,
        'active': crew.active,
        'is_applyable': crew.is_applyable,
        'hex_color': crew.hex_color
    }