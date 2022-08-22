"""Events can have an age limit

Revision ID: 8cad5b097f8b
Revises: a40ec93ac7aa
Create Date: 2022-08-22 11:24:24.454982

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8cad5b097f8b'
down_revision = 'a40ec93ac7aa'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('event', sa.Column('age_limit_inclusive', sa.Integer(), server_default='-1', nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('event', 'age_limit_inclusive')
    # ### end Alembic commands ###
