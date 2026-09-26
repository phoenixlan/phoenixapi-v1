"""ticket type mapping

Revision ID: 1b7888972f1d
Revises: 52986905717f
Create Date: 2026-09-24 16:52:00.135371

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1b7888972f1d'
down_revision = '52986905717f'
branch_labels = None
depends_on = None


def upgrade():
    # The old max_participants capped the event as a whole. It becomes the cap of the "all" group, which every
    # ticket type the event used to offer is made a member of below
    op.add_column('event', sa.Column('ticket_sales_caps', sa.JSON(), server_default='{}', nullable=False))
    op.execute("UPDATE event SET ticket_sales_caps = json_build_object('all', max_participants)")

    op.create_table('event_ticket_type_mapping',
    sa.Column('uuid', sa.UUID(), nullable=False),
    sa.Column('event_uuid', sa.UUID(), nullable=False),
    sa.Column('ticket_type_uuid', sa.UUID(), nullable=False),
    sa.Column('sales_cap', sa.Integer(), nullable=True),
    sa.Column('sales_cap_groups', sa.ARRAY(sa.Text()), nullable=False),
    sa.Column('access_code', sa.Text(), nullable=True),
    sa.Column('created', sa.DateTime(), nullable=False),
    sa.Column('modified', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['event_uuid'], ['event.uuid'], name=op.f('fk_event_ticket_type_mapping_event_uuid_event')),
    sa.ForeignKeyConstraint(['ticket_type_uuid'], ['ticket_type.uuid'], name=op.f('fk_event_ticket_type_mapping_ticket_type_uuid_ticket_type')),
    sa.PrimaryKeyConstraint('uuid', name=op.f('pk_event_ticket_type_mapping')),
    sa.UniqueConstraint('event_uuid', 'ticket_type_uuid', name='_event_tickettype_uic'),
    sa.UniqueConstraint('uuid', name=op.f('uq_event_ticket_type_mapping_uuid'))
    )
    op.create_table('user_event_ticket_type_activations',
    sa.Column('user_uuid', sa.UUID(), nullable=True),
    sa.Column('event_ticket_type_mapping_uuid', sa.UUID(), nullable=True),
    sa.ForeignKeyConstraint(['event_ticket_type_mapping_uuid'], ['event_ticket_type_mapping.uuid'], name=op.f('fk_user_event_ticket_type_activations_event_ticket_type_mapping_uuid_event_ticket_type_mapping')),
    sa.ForeignKeyConstraint(['user_uuid'], ['user.uuid'], name=op.f('fk_user_event_ticket_type_activations_user_uuid_user'))
    )

    # Map every ticket type an event used to offer: the ones statically added to it, and the ones
    # the ticket type listing deduced from rows in the event's seatmap. Each mapping belongs to the "all"
    # group, so the ticket types share the old max_participants between them
    op.execute("""
        INSERT INTO event_ticket_type_mapping
            (uuid, event_uuid, ticket_type_uuid, sales_cap, sales_cap_groups, access_code, created, modified)
        SELECT gen_random_uuid(), old_types.event_uuid, old_types.ticket_type_uuid, NULL, '{all}'::text[], NULL, NOW(), NOW()
        FROM (
            SELECT event_uuid, ticket_type_uuid
            FROM event_ticket_type_static_assoc
            WHERE event_uuid IS NOT NULL AND ticket_type_uuid IS NOT NULL
            UNION
            SELECT event.uuid, "row".ticket_type_uuid
            FROM event
            JOIN "row" ON "row".seatmap_uuid = event.seatmap_uuid
            WHERE "row".ticket_type_uuid IS NOT NULL
        ) AS old_types
        JOIN event ON event.uuid = old_types.event_uuid
    """)

    op.drop_table('event_ticket_type_static_assoc')
    op.drop_column('event', 'max_participants')


def downgrade():
    # Nullable first so existing events can be filled in. Events without an "all" group cap had no total limit, which max_participants can't express
    op.add_column('event', sa.Column('max_participants', sa.INTEGER(), autoincrement=False, nullable=True))
    op.execute("UPDATE event SET max_participants = COALESCE((ticket_sales_caps->>'all')::integer, 0)")
    op.alter_column('event', 'max_participants', existing_type=sa.INTEGER(), nullable=False)
    op.drop_column('event', 'ticket_sales_caps')

    op.create_table('event_ticket_type_static_assoc',
    sa.Column('event_uuid', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('ticket_type_uuid', sa.UUID(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['event_uuid'], ['event.uuid'], name=op.f('fk_event_ticket_type_static_assoc_event_uuid_event')),
    sa.ForeignKeyConstraint(['ticket_type_uuid'], ['ticket_type.uuid'], name=op.f('fk_event_ticket_type_static_assoc_ticket_type_uuid_ticket_type'))
    )
    # Sales caps, groups and access codes have no equivalent in the old model and are lost
    op.execute("""
        INSERT INTO event_ticket_type_static_assoc (event_uuid, ticket_type_uuid)
        SELECT event_uuid, ticket_type_uuid FROM event_ticket_type_mapping
    """)

    op.drop_table('user_event_ticket_type_activations')
    op.drop_table('event_ticket_type_mapping')
