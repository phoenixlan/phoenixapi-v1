"""Created infoscreen entry

Revision ID: 7c529d07d428
Revises: 22f3a9c508e7
Create Date: 2022-11-20 18:04:29.323800

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '7c529d07d428'
down_revision = '22f3a9c508e7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('infoscreen_entry',
    sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('event_uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('created_by_user_uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('title', sa.Text(), nullable=False),
    sa.Column('message', sa.Text(), nullable=False),
    sa.Column('start_time', sa.DateTime(), nullable=False),
    sa.Column('end_time', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['created_by_user_uuid'], ['user.uuid'], name=op.f('fk_infoscreen_entry_created_by_user_uuid_user')),
    sa.ForeignKeyConstraint(['event_uuid'], ['event.uuid'], name=op.f('fk_infoscreen_entry_event_uuid_event')),
    sa.PrimaryKeyConstraint('uuid', name=op.f('pk_infoscreen_entry')),
    sa.UniqueConstraint('uuid', name=op.f('uq_infoscreen_entry_uuid'))
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('infoscreen_entry')
    # ### end Alembic commands ###
