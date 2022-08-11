from .ticket import map_ticket_simple

def map_user_with_secret_fields(user, request):
    return {
        'uuid': str(user.uuid),
        'username': user.username,
        'birthdate': str(user.birthdate),
        'email': user.email,
        
        'firstname': user.firstname,
        'lastname': user.lastname,
        
        'birthdate': str(user.birthdate),
        'gender': str(user.gender),

        'phone': user.phone,
        'address': user.address,
        'postal_code': user.postal_code,
        'country_code': user.country_code,
        'tos_level': user.tos_level,
        'created': (user.created.timestamp()),

        'positions': user.positions,
        'avatar_uuid': user.avatar.uuid if user.avatar is not None else None,
        'avatar_urls': user.get_avatar_urls(request),

        'owned_tickets': [ map_ticket_simple(ticket) for ticket in user.owned_tickets ],
        'purchased_tickets': [ map_ticket_simple(ticket) for ticket in user.purchased_tickets ],
        'seatable_tickets': [ map_ticket_simple(ticket) for ticket in user.seatable_tickets ]
    }

def map_user_public_with_positions(user, request):
    return {
        'uuid': str(user.uuid),
        'username': user.username,
        
        'firstname': user.firstname,
        'lastname': user.lastname,
        
        'gender': str(user.gender),

        'avatar_urls': user.get_avatar_urls(request),
        'positions': user.positions
    }


def map_user_simple_with_secret_fields(user, request):
    return {
        'uuid': user.uuid,
        'username': user.username,
        'birthdate': str(user.birthdate),
        'email': user.email,
        
        'firstname': user.firstname,
        'lastname': user.lastname,
        
        'gender': str(user.gender),
        'created': (user.created.timestamp()),

        'avatar_uuid': user.avatar.uuid if user.avatar is not None else None,
        'avatar_urls': user.get_avatar_urls(request),
    }
