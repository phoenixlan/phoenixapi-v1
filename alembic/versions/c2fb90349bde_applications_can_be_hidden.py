"""Applications can be hidden

Revision ID: c2fb90349bde
Revises: ba65684cc98b
Create Date: 2023-08-27 15:35:05.482154

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c2fb90349bde'
down_revision = 'ba65684cc98b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('application', sa.Column('hidden', sa.Boolean(), nullable=False))
    op.create_unique_constraint(op.f('uq_consent_withdrawal_code_uuid'), 'consent_withdrawal_code', ['uuid'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(op.f('uq_consent_withdrawal_code_uuid'), 'consent_withdrawal_code', type_='unique')
    op.drop_column('application', 'hidden')
    # ### end Alembic commands ###
