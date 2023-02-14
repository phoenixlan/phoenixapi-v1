"""Add application crew mapping table

Revision ID: b4846647b0de
Revises: 66f31c1d0613
Create Date: 2023-01-06 16:41:11.272934

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'b4846647b0de'
down_revision = '66f31c1d0613'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('application_crew_mapping',
    sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('application_uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('crew_uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('list_order', sa.Integer(), nullable=False),
    sa.Column('created', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['application_uuid'], ['application.uuid'], name=op.f('fk_application_crew_mapping_application_uuid_application')),
    sa.ForeignKeyConstraint(['crew_uuid'], ['crew.uuid'], name=op.f('fk_application_crew_mapping_crew_uuid_crew')),
    sa.PrimaryKeyConstraint('uuid', name=op.f('pk_application_crew_mapping')),
    sa.UniqueConstraint('application_uuid', 'crew_uuid', 'list_order', name='_application_crew_mapping_uic'),
    sa.UniqueConstraint('uuid', name=op.f('uq_application_crew_mapping_uuid'))
    )
    op.execute("""INSERT INTO application_crew_mapping(uuid, list_order, created, application_uuid, crew_uuid) 
        SELECT gen_random_uuid(), 0, NOW(), uuid, crew_uuid from application
    """);
    op.add_column('application_crew_mapping', sa.Column('accepted', sa.Boolean(), server_default='false', nullable=False))
    op.drop_constraint('fk_application_crew_uuid_crew', 'application', type_='foreignkey')
    op.drop_column('application', 'crew_uuid')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('_user_positionmapping_uic', 'user_positions', type_='unique')
    op.add_column('application', sa.Column('crew_uuid', postgresql.UUID(), autoincrement=False, nullable=False))
    op.create_foreign_key('fk_application_crew_uuid_crew', 'application', 'crew', ['crew_uuid'], ['uuid'])
    op.drop_table('application_crew_mapping')
    # ### end Alembic commands ###