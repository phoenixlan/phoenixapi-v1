from .ticket import map_ticket_simple
from .position_mapping import map_position_mapping_with_position

def map_user_with_secret_fields(user, request):
    return {
        'uuid': str(user.uuid),
        'birthdate': str(user.birthdate),
        'email': user.email,
        
        'firstname': user.firstname,
        'lastname': user.lastname,
        
        'gender': str(user.gender),

        'guardian_phone': user.guardian_phone,

        'tos_level': user.tos_level,
        'created': int(user.created.timestamp()),

        'position_mappings': [ map_position_mapping_with_position(mapping) for mapping in user.position_mappings ],
        'avatar_uuid': user.avatar.uuid if user.avatar is not None else None,
        'avatar_urls': user.get_avatar_urls(request),

        'consents': user.consents
    }

def map_user_with_secret_fields_member_personalia(user, request):
    return {
        'uuid': str(user.uuid),
        'birthdate': str(user.birthdate),
        'email': user.email,
        
        'firstname': user.firstname,
        'lastname': user.lastname,
        
        'gender': str(user.gender),

        'guardian_phone': user.guardian_phone,

        'member_personalia': user.member_personalia if user.member_personalia is not None else None,

        'tos_level': user.tos_level,
        'created': int(user.created.timestamp()),
    }

def map_user_public_with_positions(user, request):
    return {
        'uuid': str(user.uuid),
        
        'firstname': user.firstname,
        'lastname': user.lastname,
        
        'gender': str(user.gender),

        'avatar_urls': user.get_avatar_urls(request),
        'position_mappings': [map_position_mapping_with_position(mapping) for mapping in user.position_mappings],
    }


def map_user_simple_with_secret_fields(user, request):
    return {
        'uuid': user.uuid,
        'birthdate': str(user.birthdate),
        'email': user.email,

        'guardian_phone': user.guardian_phone,

        'firstname': user.firstname,
        'lastname': user.lastname,
        
        'gender': str(user.gender),
        'created': int(user.created.timestamp()),

        'avatar_uuid': user.avatar.uuid if user.avatar is not None else None,
        'avatar_urls': user.get_avatar_urls(request),
    }
