from phoenixRest.mappers.user import map_user_no_positions

def map_position_no_crew(position, request):
	return {
        'uuid': position.uuid,
        'name': position.name,
        'description': position.description,

        'crew': position.crew_uuid,
        'team': position.team_uuid,
        'users': [map_user_no_positions(user) for user in position.users],
        'chief': position.chief,
        'permissions': position.permissions

    }