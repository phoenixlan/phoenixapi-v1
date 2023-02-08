"""Initial migration

Revision ID: 69f2b77c9ef1
Revises: 
Create Date: 2022-08-04 16:26:53.655662

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from datetime import datetime, date

import uuid

# revision identifiers, used by Alembic.
revision = '69f2b77c9ef1'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    crew_table = op.create_table('crew',
    sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.Column('is_applyable', sa.Boolean(), nullable=False),
    sa.Column('hex_color', sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint('uuid', name=op.f('pk_crew')),
    sa.UniqueConstraint('uuid', name=op.f('uq_crew_uuid'))
    )

    core_uuid = uuid.uuid4()
    tech_uuid = uuid.uuid4()
    op.bulk_insert(crew_table,
        [
            {
                'uuid':core_uuid, 
                'name': 'Core', 
                'description': 'Insane in the membrane',
                'active': True,
                'is_applyable': False,
                'hex_color': '#CDDC39',
            },
            {
                'uuid':uuid.uuid4(), 
                'name': 'Game', 
                'description': 'Only real gamers',
                'active': True,
                'is_applyable': True,
                'hex_color': '#009688',
            },
            {
                'uuid':uuid.uuid4(), 
                'name': 'Kafe og Backstage', 
                'description': 'Yamu yamu piza piza',
                'active': True,
                'is_applyable': True,
                'hex_color': '#2196F3',
            },
            {
                'uuid':uuid.uuid4(), 
                'name': 'Media', 
                'description': 'Linselus',
                'active': True,
                'is_applyable': True,
                'hex_color': '#8BC34A',
            },
            {
                'uuid':uuid.uuid4(), 
                'name': 'Security', 
                'description': 'Oi! You got a loicense?',
                'active': True,
                'is_applyable': True,
                'hex_color': '#000000',
            },
            {
                'uuid':uuid.uuid4(), 
                'name': 'Social', 
                'description': 'Socializing is our thing',
                'active': True,
                'is_applyable': True,
                'hex_color': '#FF00AA',
            },
            {
                'uuid':tech_uuid, 
                'name': 'Tech', 
                'description': 'Technical stuff',
                'active': True,
                'is_applyable': True,
                'hex_color': '#FF5722',
            },
            {
                'uuid':uuid.uuid4(), 
                'name': 'Secret crew', 
                'description': 'Test that inactive crews are hidden',
                'active': False,
                'is_applyable': True, 
                'hex_color': '#009688',
            },
        ]
    )


    entrance_table = op.create_table('entrance',
    sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint('uuid', name=op.f('pk_entrance')),
    sa.UniqueConstraint('uuid', name=op.f('uq_entrance_uuid'))
    )

    library_uuid = uuid.uuid4()
    op.bulk_insert(entrance_table,
        [
            {
                'uuid':uuid.uuid4(), 
                'name': 'Radar Cafe',
            },
            {
                'uuid': library_uuid, 
                'name': 'Bibilioteket',
            },
            
        ]
    )

    ticket_type_table = op.create_table('ticket_type',
    sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('price', sa.Integer(), nullable=False),
    sa.Column('refundable', sa.Boolean(), nullable=False),
    sa.Column('seatable', sa.Boolean(), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('uuid', name=op.f('pk_ticket_type')),
    sa.UniqueConstraint('uuid', name=op.f('uq_ticket_type_uuid'))
    )

    ticket_type_multi = uuid.uuid4()
    ticket_type_exp = uuid.uuid4()

    op.bulk_insert(ticket_type_table, 
        [
            {
                'uuid': ticket_type_multi,
                'name': 'Multisal',
                'price': 350,
                'refundable': True,
                'seatable': True,
                'description': 'Gir deg plass i multisalen'
            },
            {
                'uuid': ticket_type_exp,
                'name': 'Vestibyle',
                'price': 450,
                'refundable': True,
                'seatable': True,
                'description': 'Gir deg plass i vestibylen'
            },
            {
                'uuid': uuid.uuid4(),
                'name': 'Gratis',
                'price': 0,
                'refundable': False,
                'seatable': True,
                'description': 'Gratisbillett'
            }
        ]
    )

    user_table = op.create_table('user',
    sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('email', sa.Text(), nullable=False),
    sa.Column('username', sa.Text(), nullable=False),
    sa.Column('firstname', sa.Text(), nullable=False),
    sa.Column('lastname', sa.Text(), nullable=False),
    sa.Column('birthdate', sa.Date(), nullable=False),
    sa.Column('gender', sa.Enum('male', 'female', name='gender'), nullable=False),
    sa.Column('phone', sa.Text(), nullable=False),
    sa.Column('guardian_phone', sa.Text(), nullable=True),
    sa.Column('address', sa.Text(), nullable=False),
    sa.Column('postal_code', sa.Text(), nullable=False),
    sa.Column('country_code', sa.Text(), nullable=False),
    sa.Column('tos_level', sa.Integer(), nullable=False),
    sa.Column('password', sa.Text(), nullable=False),
    sa.Column('password_type', sa.Integer(), nullable=False),
    sa.Column('created', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('uuid', name=op.f('pk_user')),
    sa.UniqueConstraint('email', name=op.f('uq_user_email')),
    sa.UniqueConstraint('username', name=op.f('uq_user_username')),
    sa.UniqueConstraint('uuid', name=op.f('uq_user_uuid'))
    )

    test_account_uuid = uuid.uuid4()

    greg_uuid = uuid.uuid4()
    jeff_uuid = uuid.uuid4()
    adam_uuid = uuid.uuid4()

    op.bulk_insert(user_table,
        [
            {
                'uuid':test_account_uuid, 
                'email': 'test@example.com', 
                'username': 'test',
                'password': 'Not-used',
                'password_type': 2,
                'created': datetime.now(),
                'address': '1. Mann. Co rd',
                'birthdate': date(1998, 3, 27),
                'country_code': 'no',
                'firstname': 'Test',
                'lastname': 'Testesen',
                'gender': 'male',
                'phone': '98643254', # Vipps test number
                'postal_code': '1395',
                'tos_level': 0
            },
            {
                'uuid':greg_uuid, 
                'email': 'greg@example.com', 
                'username': 'greg',
                'password': 'Not-used',
                'password_type': 2,
                'created': datetime.now(),
                'address': '1. Mann. Co rd',
                'birthdate': date(1998, 3, 27),
                'country_code': 'no',
                'firstname': 'Greg',
                'lastname': 'Gregsson',
                'gender': 'male',
                'phone': '99999999',
                'postal_code': '1395',
                'tos_level': 0
            },
            {
                'uuid':jeff_uuid, 
                'email': 'jeff@example.com', 
                'username': 'jeff',
                'password': 'Not-used',
                'password_type': 2,
                'created': datetime.now(),
                'address': '1. Mann. Co rd',
                'birthdate': date(1998, 3, 27),
                'country_code': 'no',
                'firstname': 'Jeff',
                'lastname': 'Jefferson',
                'gender': 'male',
                'phone': '99999999',
                'postal_code': '1395',
                'tos_level': 0
            },
            {
                'uuid':adam_uuid, 
                'email': 'adam@example.com', 
                'username': 'adam',
                'password': 'Not-used',
                'password_type': 2,
                'created': datetime.now(),
                'address': '1. Mann. Co rd',
                'birthdate': date(1998, 3, 27),
                'country_code': 'no',
                'firstname': 'Adam',
                'lastname': 'Adamson',
                'gender': 'male',
                'phone': '99999999',
                'postal_code': '1395',
                'tos_level': 0
            },
        ]
    )

    op.create_table('activation_code',
    sa.Column('user_uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('code', sa.Text(), nullable=False),
    sa.Column('client_id', sa.Text(), nullable=True),
    sa.Column('created', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_uuid'], ['user.uuid'], name=op.f('fk_activation_code_user_uuid_user')),
    sa.PrimaryKeyConstraint('user_uuid', 'code', name=op.f('pk_activation_code'))
    )
    op.create_table('avatar',
    sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('state', sa.Enum('uploaded', 'accepted', 'rejected', name='avatarstate'), nullable=False),
    sa.Column('user_uuid', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('created', sa.DateTime(), nullable=False),
    sa.Column('extension', sa.Text(), nullable=False),
    sa.ForeignKeyConstraint(['user_uuid'], ['user.uuid'], name=op.f('fk_avatar_user_uuid_user')),
    sa.PrimaryKeyConstraint('uuid', name=op.f('pk_avatar')),
    sa.UniqueConstraint('uuid', name=op.f('uq_avatar_uuid'))
    )
    op.create_table('oauth_code',
    sa.Column('code', sa.Text(), nullable=False),
    sa.Column('user_uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('expires', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_uuid'], ['user.uuid'], name=op.f('fk_oauth_code_user_uuid_user')),
    sa.PrimaryKeyConstraint('code', name=op.f('pk_oauth_code')),
    sa.UniqueConstraint('code', name=op.f('uq_oauth_code_code'))
    )
    op.create_table('oauth_refresh_token',
    sa.Column('token', sa.Text(), nullable=False),
    sa.Column('user_uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('user_agent', sa.Text(), nullable=False),
    sa.Column('created', sa.DateTime(), nullable=False),
    sa.Column('expires', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_uuid'], ['user.uuid'], name=op.f('fk_oauth_refresh_token_user_uuid_user')),
    sa.PrimaryKeyConstraint('token', name=op.f('pk_oauth_refresh_token')),
    sa.UniqueConstraint('token', name=op.f('uq_oauth_refresh_token_token'))
    )
    op.create_table('seatmap_background',
    sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('created', sa.DateTime(), server_default='NOW()', nullable=False),
    sa.Column('extension', sa.Text(), nullable=False),
    sa.Column('uploader_uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.ForeignKeyConstraint(['uploader_uuid'], ['user.uuid'], name=op.f('fk_seatmap_background_uploader_uuid_user')),
    sa.PrimaryKeyConstraint('uuid', name=op.f('pk_seatmap_background')),
    sa.UniqueConstraint('uuid', name=op.f('uq_seatmap_background_uuid'))
    )
    op.create_table('store_session',
    sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('user_uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('created', sa.DateTime(), nullable=False),
    sa.Column('expires', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_uuid'], ['user.uuid'], name=op.f('fk_store_session_user_uuid_user')),
    sa.PrimaryKeyConstraint('uuid', name=op.f('pk_store_session')),
    sa.UniqueConstraint('uuid', name=op.f('uq_store_session_uuid'))
    )
    team_table = op.create_table('team',
    sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('crew_uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.ForeignKeyConstraint(['crew_uuid'], ['crew.uuid'], name=op.f('fk_team_crew_uuid_crew')),
    sa.PrimaryKeyConstraint('uuid', name=op.f('pk_team')),
    sa.UniqueConstraint('uuid', name=op.f('uq_team_uuid'))
    )

    barnehage_team = uuid.uuid4()
    swag_team_uuid = uuid.uuid4()

    op.bulk_insert(team_table, [
        {
            'uuid': barnehage_team,
            'name': 'Barnehagen',
            'description': 'What a ruckus',
            'crew_uuid': core_uuid
        },
        {
            'uuid': swag_team_uuid,
            'name': 'Swag team 1',
            'description': 'Hell yeah',
            'crew_uuid': core_uuid
        }
    ])

    op.create_table('payment',
    sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('user_uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('store_session_uuid', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('provider', sa.Enum('vipps', 'stripe', name='paymentprovider'), nullable=False),
    sa.Column('state', sa.Enum('created', 'initiated', 'paid', 'failed', 'tickets_minted', name='paymentstate'), nullable=False),
    sa.Column('price', sa.Integer(), nullable=False),
    sa.Column('created', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['store_session_uuid'], ['store_session.uuid'], name=op.f('fk_payment_store_session_uuid_store_session')),
    sa.ForeignKeyConstraint(['user_uuid'], ['user.uuid'], name=op.f('fk_payment_user_uuid_user')),
    sa.PrimaryKeyConstraint('uuid', name=op.f('pk_payment')),
    sa.UniqueConstraint('uuid', name=op.f('uq_payment_uuid'))
    )
    position_table = op.create_table('position',
    sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('crew_uuid', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('team_uuid', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('name', sa.Text(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('chief', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['crew_uuid'], ['crew.uuid'], name=op.f('fk_position_crew_uuid_crew')),
    sa.ForeignKeyConstraint(['team_uuid'], ['team.uuid'], name=op.f('fk_position_team_uuid_team')),
    sa.PrimaryKeyConstraint('uuid', name=op.f('pk_position')),
    sa.UniqueConstraint('uuid', name=op.f('uq_position_uuid'))
    )

    # Give the user some goddamn access
    admin_position_uuid = uuid.uuid4()

    core_member_uuid = uuid.uuid4()
    core_swag_uuid = uuid.uuid4()
    core_barnehage_uuid = uuid.uuid4()


    tech_chief_uuid = uuid.uuid4()

    op.bulk_insert(position_table,
        [
            {
                'uuid':admin_position_uuid, 
                'crew_uuid': None, 
                'team_uuid': None,
                'name': 'Superadmin',
                'chief': False
            },
            {
                'uuid':core_member_uuid, 
                'crew_uuid': core_uuid, 
                'team_uuid': None,
                'name': None,
                'chief': False
            },
            {
                'uuid':core_swag_uuid, 
                'crew_uuid': core_uuid, 
                'team_uuid': swag_team_uuid,
                'name': None,
                'chief': False
            },
            {
                'uuid':core_barnehage_uuid, 
                'crew_uuid': core_uuid, 
                'team_uuid': barnehage_team,
                'name': None,
                'chief': False
            },
            {
                'uuid':tech_chief_uuid, 
                'crew_uuid': tech_uuid, 
                'team_uuid': None,
                'name': None,
                'chief': True
            },
        ]
    )

    op.create_table('seatmap',
    sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('background_uuid', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('width', sa.Integer(), server_default='600', nullable=True),
    sa.Column('height', sa.Integer(), server_default='800', nullable=True),
    sa.ForeignKeyConstraint(['background_uuid'], ['seatmap_background.uuid'], name=op.f('fk_seatmap_background_uuid_seatmap_background')),
    sa.PrimaryKeyConstraint('uuid', name=op.f('pk_seatmap')),
    sa.UniqueConstraint('uuid', name=op.f('uq_seatmap_uuid'))
    )
    op.create_table('store_session_cart_entry',
    sa.Column('store_session_uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('ticket_type_uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('amount', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['store_session_uuid'], ['store_session.uuid'], name=op.f('fk_store_session_cart_entry_store_session_uuid_store_session')),
    sa.ForeignKeyConstraint(['ticket_type_uuid'], ['ticket_type.uuid'], name=op.f('fk_store_session_cart_entry_ticket_type_uuid_ticket_type')),
    sa.PrimaryKeyConstraint('store_session_uuid', 'ticket_type_uuid', name=op.f('pk_store_session_cart_entry'))
    )

    first_event_uuid = uuid.uuid4()

    event_table = op.create_table('event',
    sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('booking_time', sa.DateTime(), nullable=False),
    sa.Column('priority_seating_time_delta', sa.Integer(), nullable=False),
    sa.Column('seating_time_delta', sa.Integer(), nullable=False),
    sa.Column('start_time', sa.DateTime(), nullable=False),
    sa.Column('end_time', sa.DateTime(), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('theme', sa.Text(), nullable=True),
    sa.Column('max_participants', sa.Integer(), nullable=False),
    sa.Column('seatmap_uuid', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('cancellation_reason', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['seatmap_uuid'], ['seatmap.uuid'], name=op.f('fk_event_seatmap_uuid_seatmap')),
    sa.PrimaryKeyConstraint('uuid', name=op.f('pk_event')),
    sa.UniqueConstraint('uuid', name=op.f('uq_event_uuid'))
    )

    # Seed the event table with some data
    op.bulk_insert(event_table,
        [
            {
                'uuid':first_event_uuid,
                'name': "event 1",
                'booking_time': datetime.strptime('2021-09-01 18:00:00', '%Y-%m-%d %H:%M:%S'), 
                'priority_seating_time_delta': 60*30,
                'seating_time_delta': 60*60,
                'start_time': datetime.strptime('2021-10-01 18:00:00', '%Y-%m-%d %H:%M:%S'),
                'end_time': datetime.strptime('2021-10-03 12:00:00', '%Y-%m-%d %H:%M:%S'),
                'max_participants': 400
            },
            {
                'uuid':uuid.uuid4(), 
                'name': "event 2",
                'booking_time': datetime.strptime('2022-01-18 18:00:00', '%Y-%m-%d %H:%M:%S'), 
                'priority_seating_time_delta': 60*30,
                'seating_time_delta': 60*60,
                'start_time': datetime.strptime('2022-02-18 18:00:00', '%Y-%m-%d %H:%M:%S'),
                'end_time': datetime.strptime('2022-02-20 12:00:00', '%Y-%m-%d %H:%M:%S'),
                'max_participants': 400
            },
            {
                'uuid':uuid.uuid4(), 
                'name': "event 3",
                'booking_time': datetime.strptime('2022-08-30 18:00:00', '%Y-%m-%d %H:%M:%S'), 
                'priority_seating_time_delta': 60*30,
                'seating_time_delta': 60*60,
                'start_time': datetime.strptime('2022-09-30 18:00:00', '%Y-%m-%d %H:%M:%S'),
                'end_time': datetime.strptime('2022-10-02 12:00:00', '%Y-%m-%d %H:%M:%S'),
                'max_participants': 400
            },
            {
                'uuid':uuid.uuid4(), 
                'name': "event 4",
                'booking_time': datetime.strptime('2023-01-17 18:00:00', '%Y-%m-%d %H:%M:%S'), 
                'priority_seating_time_delta': 60*30,
                'seating_time_delta': 60*60,
                'start_time': datetime.strptime('2023-02-17 18:00:00', '%Y-%m-%d %H:%M:%S'),
                'end_time': datetime.strptime('2023-02-19 12:00:00', '%Y-%m-%d %H:%M:%S'),
                'max_participants': 400
            }
        ]
    )

    op.create_table('row',
    sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('row_number', sa.Integer(), nullable=False),
    sa.Column('x', sa.Integer(), nullable=False),
    sa.Column('y', sa.Integer(), nullable=False),
    sa.Column('is_horizontal', sa.Boolean(), nullable=False),
    sa.Column('ticket_type_uuid', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('seatmap_uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('entrance_uuid', postgresql.UUID(as_uuid=True), nullable=True),
    sa.ForeignKeyConstraint(['entrance_uuid'], ['entrance.uuid'], name=op.f('fk_row_entrance_uuid_entrance')),
    sa.ForeignKeyConstraint(['seatmap_uuid'], ['seatmap.uuid'], name=op.f('fk_row_seatmap_uuid_seatmap')),
    sa.ForeignKeyConstraint(['ticket_type_uuid'], ['ticket_type.uuid'], name=op.f('fk_row_ticket_type_uuid_ticket_type')),
    sa.PrimaryKeyConstraint('uuid', name=op.f('pk_row')),
    sa.UniqueConstraint('uuid', name=op.f('uq_row_uuid'))
    )
    op.create_table('stripe_payment',
    sa.Column('payment_uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('client_secret', sa.Text(), nullable=False),
    sa.Column('paid', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['payment_uuid'], ['payment.uuid'], name=op.f('fk_stripe_payment_payment_uuid_payment')),
    sa.PrimaryKeyConstraint('payment_uuid', name=op.f('pk_stripe_payment'))
    )
    position_binding_table = op.create_table('user_positions',
    sa.Column('user_uuid', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('position_uuid', postgresql.UUID(as_uuid=True), nullable=True),
    sa.ForeignKeyConstraint(['position_uuid'], ['position.uuid'], name=op.f('fk_user_positions_position_uuid_position')),
    sa.ForeignKeyConstraint(['user_uuid'], ['user.uuid'], name=op.f('fk_user_positions_user_uuid_user'))
    )

    op.bulk_insert(position_binding_table,
        [
            {
                'user_uuid':test_account_uuid, 
                'position_uuid': admin_position_uuid, 
            },
            {
                'user_uuid':test_account_uuid, 
                'position_uuid': core_member_uuid, 
            },
            {
                'user_uuid':test_account_uuid, 
                'position_uuid': tech_chief_uuid, 
            },
            # Other test users
            {
                'user_uuid':greg_uuid, 
                'position_uuid': core_swag_uuid, 
            },
            {
                'user_uuid':jeff_uuid, 
                'position_uuid': core_barnehage_uuid, 
            }
        ]
    )

    op.create_table('vipps_payment',
    sa.Column('payment_uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('slug', sa.Text(), nullable=False),
    sa.Column('order_id', sa.Text(), nullable=True),
    sa.Column('state', sa.Text(), nullable=False),
    sa.ForeignKeyConstraint(['payment_uuid'], ['payment.uuid'], name=op.f('fk_vipps_payment_payment_uuid_payment')),
    sa.PrimaryKeyConstraint('payment_uuid', name=op.f('pk_vipps_payment')),
    sa.UniqueConstraint('slug', name=op.f('uq_vipps_payment_slug'))
    )
    op.create_table('agenda_entry',
    sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('event_uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('time', sa.DateTime(), nullable=False),
    sa.Column('title', sa.Text(), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.ForeignKeyConstraint(['event_uuid'], ['event.uuid'], name=op.f('fk_agenda_entry_event_uuid_event')),
    sa.PrimaryKeyConstraint('uuid', name=op.f('pk_agenda_entry')),
    sa.UniqueConstraint('uuid', name=op.f('uq_agenda_entry_uuid'))
    )
    op.create_table('application',
    sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('crew_uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('event_uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('user_uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('contents', sa.Text(), nullable=False),
    sa.Column('created', sa.DateTime(), nullable=False),
    sa.Column('answer', sa.Text(), nullable=False),
    sa.Column('last_processed_by_uuid', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('state', sa.Enum('created', 'accepted', 'rejected', name='applicationstate'), nullable=False),
    sa.ForeignKeyConstraint(['crew_uuid'], ['crew.uuid'], name=op.f('fk_application_crew_uuid_crew')),
    sa.ForeignKeyConstraint(['event_uuid'], ['event.uuid'], name=op.f('fk_application_event_uuid_event')),
    sa.ForeignKeyConstraint(['last_processed_by_uuid'], ['user.uuid'], name=op.f('fk_application_last_processed_by_uuid_user')),
    sa.ForeignKeyConstraint(['user_uuid'], ['user.uuid'], name=op.f('fk_application_user_uuid_user')),
    sa.PrimaryKeyConstraint('uuid', name=op.f('pk_application')),
    sa.UniqueConstraint('uuid', name=op.f('uq_application_uuid'))
    )
    op.create_table('event_ticket_type_static_assoc',
    sa.Column('event_uuid', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('ticket_type_uuid', postgresql.UUID(as_uuid=True), nullable=True),
    sa.ForeignKeyConstraint(['event_uuid'], ['event.uuid'], name=op.f('fk_event_ticket_type_static_assoc_event_uuid_event')),
    sa.ForeignKeyConstraint(['ticket_type_uuid'], ['ticket_type.uuid'], name=op.f('fk_event_ticket_type_static_assoc_ticket_type_uuid_ticket_type'))
    )
    permission_binding_table = op.create_table('permission_binding',
    sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('position_uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('event_uuid', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('permission', sa.Text(), nullable=False),
    sa.ForeignKeyConstraint(['event_uuid'], ['event.uuid'], name=op.f('fk_permission_binding_event_uuid_event')),
    sa.ForeignKeyConstraint(['position_uuid'], ['position.uuid'], name=op.f('fk_permission_binding_position_uuid_position')),
    sa.PrimaryKeyConstraint('uuid', name=op.f('pk_permission_binding')),
    sa.UniqueConstraint('uuid', name=op.f('uq_permission_binding_uuid'))
    )

    op.bulk_insert(permission_binding_table,
        [
            {
                'uuid':uuid.uuid4(), 
                'position_uuid': admin_position_uuid, 
                'event_uuid': None,
                'permission': 'admin'
            },
            {
                'uuid':uuid.uuid4(), 
                'position_uuid': admin_position_uuid, 
                'event_uuid': None,
                'permission': 'ticket_bypass_ticketsale_start_restriction'
            },
            {
                'uuid':uuid.uuid4(), 
                'position_uuid': admin_position_uuid, 
                'event_uuid': None,
                'permission': 'ticket_wholesale'
            },
        ]
    )

    op.create_table('seat',
    sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('number', sa.Integer(), nullable=False),
    sa.Column('is_reserved', sa.Boolean(), nullable=True),
    sa.Column('row_uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.ForeignKeyConstraint(['row_uuid'], ['row.uuid'], name=op.f('fk_seat_row_uuid_row')),
    sa.PrimaryKeyConstraint('uuid', name=op.f('pk_seat')),
    sa.UniqueConstraint('uuid', name=op.f('uq_seat_uuid'))
    )
    op.create_table('ticket',
    sa.Column('ticket_id', sa.Integer(), sa.Identity(always=False, start=1, cycle=False), nullable=False),
    sa.Column('buyer_uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('owner_uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('seater_uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('payment_uuid', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('ticket_type_uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('event_uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('seat_uuid', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('created', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['buyer_uuid'], ['user.uuid'], name=op.f('fk_ticket_buyer_uuid_user')),
    sa.ForeignKeyConstraint(['event_uuid'], ['event.uuid'], name=op.f('fk_ticket_event_uuid_event')),
    sa.ForeignKeyConstraint(['owner_uuid'], ['user.uuid'], name=op.f('fk_ticket_owner_uuid_user')),
    sa.ForeignKeyConstraint(['payment_uuid'], ['payment.uuid'], name=op.f('fk_ticket_payment_uuid_payment')),
    sa.ForeignKeyConstraint(['seat_uuid'], ['seat.uuid'], name=op.f('fk_ticket_seat_uuid_seat')),
    sa.ForeignKeyConstraint(['seater_uuid'], ['user.uuid'], name=op.f('fk_ticket_seater_uuid_user')),
    sa.ForeignKeyConstraint(['ticket_type_uuid'], ['ticket_type.uuid'], name=op.f('fk_ticket_ticket_type_uuid_ticket_type')),
    sa.PrimaryKeyConstraint('ticket_id', name=op.f('pk_ticket'))
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('ticket')
    op.drop_table('seat')
    op.drop_table('permission_binding')
    op.drop_table('event_ticket_type_static_assoc')
    op.drop_table('application')
    op.drop_table('agenda_entry')
    op.drop_table('vipps_payment')
    op.drop_table('user_positions')
    op.drop_table('stripe_payment')
    op.drop_table('row')
    op.drop_table('event')
    op.drop_table('store_session_cart_entry')
    op.drop_table('seatmap')
    op.drop_table('position')
    op.drop_table('payment')
    op.drop_table('team')
    op.drop_table('store_session')
    op.drop_table('seatmap_background')
    op.drop_table('oauth_refresh_token')
    op.drop_table('oauth_code')
    op.drop_table('avatar')
    op.drop_table('activation_code')
    op.drop_table('user')
    op.drop_table('ticket_type')
    op.drop_table('entrance')
    op.drop_table('crew')
    # ### end Alembic commands ###
