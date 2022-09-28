def map_position_with_users(position, request):
	return {
        'uuid': position.uuid,
        'name': position.name,
        'description': position.description,

        'crew_uuid': position.crew_uuid,
        'team_uuid': position.team_uuid,
        'users': position.users,
        'chief': position.chief,
        'permissions': position.permissions

    }