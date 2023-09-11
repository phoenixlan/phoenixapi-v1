"""improved_agenda_system

Revision ID: b94b6a0a3aeb
Revises: 21cbd812c638
Create Date: 2023-09-09 22:51:22.670977

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b94b6a0a3aeb'
down_revision = '21cbd812c638'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('agenda_entry', sa.Column('location', sa.Text(), nullable=True))
    op.add_column('agenda_entry', sa.Column('deviating_time', sa.DateTime(), nullable=True))
    op.add_column('agenda_entry', sa.Column('deviating_time_unknown', sa.Boolean(), server_default='false', nullable=True))
    op.add_column('agenda_entry', sa.Column('deviating_location', sa.Text(), nullable=True))
    op.add_column('agenda_entry', sa.Column('deviating_information', sa.Text(), nullable=True))
    op.add_column('agenda_entry', sa.Column('pinned', sa.Boolean(), server_default='false', nullable=True))
    op.add_column('agenda_entry', sa.Column('cancelled', sa.Boolean(), server_default='false', nullable=True))
    op.add_column('agenda_entry', sa.Column('created_by_user_uuid', sa.UUID(), nullable=False))
    op.add_column('agenda_entry', sa.Column('modified_by_user_uuid', sa.UUID(), nullable=True))
    op.add_column('agenda_entry', sa.Column('created', sa.DateTime(), server_default='NOW()', nullable=False))
    op.add_column('agenda_entry', sa.Column('modified', sa.DateTime(), nullable=True))
    op.alter_column('agenda_entry', 'description', existing_type=sa.TEXT(), nullable=True)
    op.create_foreign_key(op.f('fk_agenda_entry_modified_by_user_uuid_user'), 'agenda_entry', 'user', ['modified_by_user_uuid'], ['uuid'])
    op.create_foreign_key(op.f('fk_agenda_entry_created_by_user_uuid_user'), 'agenda_entry', 'user', ['created_by_user_uuid'], ['uuid'])
    op.create_unique_constraint(op.f('uq_friendship_uuid'), 'friendship', ['uuid'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(op.f('uq_friendship_uuid'), 'friendship', type_='unique')
    op.drop_constraint(op.f('fk_agenda_entry_created_by_user_uuid_user'), 'agenda_entry', type_='foreignkey')
    op.drop_constraint(op.f('fk_agenda_entry_modified_by_user_uuid_user'), 'agenda_entry', type_='foreignkey')
    op.alter_column('agenda_entry', 'description', existing_type=sa.TEXT(), nullable=False)
    op.drop_column('agenda_entry', 'modified')
    op.drop_column('agenda_entry', 'created')
    op.drop_column('agenda_entry', 'modified_by_user_uuid')
    op.drop_column('agenda_entry', 'created_by_user_uuid')
    op.drop_column('agenda_entry', 'cancelled')
    op.drop_column('agenda_entry', 'pinned')
    op.drop_column('agenda_entry', 'deviating_information')
    op.drop_column('agenda_entry', 'deviating_location')
    op.drop_column('agenda_entry', 'deviating_time_unknown')
    op.drop_column('agenda_entry', 'deviating_time')
    op.drop_column('agenda_entry', 'location')
    # ### end Alembic commands ###
