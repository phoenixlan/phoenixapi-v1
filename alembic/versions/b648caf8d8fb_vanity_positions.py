"""Vanity positions

Revision ID: b648caf8d8fb
Revises: 358486e14fb6
Create Date: 2024-09-26 12:54:07.621931

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b648caf8d8fb'
down_revision = '358486e14fb6'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(op.f('uq_card_order_uuid'), 'card_order', ['uuid'])
    op.add_column('position', sa.Column('is_vanity', sa.Boolean(), server_default='False', nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('position', 'is_vanity')
    op.drop_constraint(op.f('uq_card_order_uuid'), 'card_order', type_='unique')
    # ### end Alembic commands ###
