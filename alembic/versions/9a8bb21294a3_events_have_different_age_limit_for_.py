"""Events have different age limit for crew and participant

Revision ID: 9a8bb21294a3
Revises: b4846647b0de
Create Date: 2023-01-08 05:46:54.114829

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9a8bb21294a3'
down_revision = 'b4846647b0de'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(op.f('uq_application_crew_mapping_uuid'), 'application_crew_mapping', ['uuid'])
    op.add_column('event', sa.Column('crew_age_limit_inclusive', sa.Integer(), server_default='-1', nullable=False))
    op.alter_column('event', 'age_limit_inclusive', new_column_name='participant_age_limit_inclusive')
    op.create_unique_constraint('_user_positionmapping_uic', 'user_positions', ['position_uuid', 'user_uuid', 'event_uuid'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('_user_positionmapping_uic', 'user_positions', type_='unique')
    op.drop_column('event', 'crew_age_limit_inclusive')
    op.alter_column('event', 'participant_age_limit_inclusive', new_column_name='age_limit_inclusive')
    op.drop_constraint(op.f('uq_application_crew_mapping_uuid'), 'application_crew_mapping', type_='unique')
    # ### end Alembic commands ###
