from .ticket import map_ticket_simple

def map_user_with_secret_fields(user):
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

        'positions': user.positions,
        'avatar': user.avatar,

        'owned_tickets': [ map_ticket_simple(ticket) for ticket in user.owned_tickets ],
        'purchased_tickets': [ map_ticket_simple(ticket) for ticket in user.purchased_tickets ],
        'seatable_tickets': [ map_ticket_simple(ticket) for ticket in user.seatable_tickets ]
    }

def map_user_no_positions(user):
    return {
        'uuid': user.uuid,
        'username': user.username,
        
        'firstname': user.firstname,
        'lastname': user.lastname,
        
        'gender': str(user.gender),

        'avatar': user.avatar
    }

def map_user_public_with_positions(user):
    return {
        'uuid': str(user.uuid),
        'username': user.username,
        
        'firstname': user.firstname,
        'lastname': user.lastname,
        
        'gender': str(user.gender),

        'avatar': user.avatar,
        'positions': user.positions
    }


def map_user_simple_with_secret_fields(user):
    return {
        'uuid': user.uuid,
        'username': user.username,
        'birthdate': str(user.birthdate),
        'email': user.email,
        
        'firstname': user.firstname,
        'lastname': user.lastname,
        
        'gender': str(user.gender),
    }

def map_user_simple(user):
    return {
        'uuid': user.uuid,
        'username': user.username,
        'birthdate': str(user.birthdate),
        
        'firstname': user.firstname,
        'lastname': user.lastname,
        
        'gender': str(user.gender),
    }