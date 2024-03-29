"""Add consent withdrawal code

Revision ID: ba65684cc98b
Revises: 2d7a36f1a5a5
Create Date: 2023-08-20 13:07:34.056511

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'ba65684cc98b'
down_revision = '2d7a36f1a5a5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('consent_withdrawal_code',
    sa.Column('uuid', sa.UUID(), nullable=False),
    sa.Column('consent_type', postgresql.ENUM('event_notification', name='consenttype', create_type=False), nullable=False),
    sa.Column('user_uuid', sa.UUID(), nullable=False),
    sa.Column('created', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_uuid'], ['user.uuid'], name=op.f('fk_consent_withdrawal_code_user_uuid_user')),
    sa.PrimaryKeyConstraint('uuid', name=op.f('pk_consent_withdrawal_code')),
    sa.UniqueConstraint('uuid', name=op.f('uq_consent_withdrawal_code_uuid'))
    )
    op.create_unique_constraint(op.f('uq_ticket_voucher_uuid'), 'ticket_voucher', ['uuid'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(op.f('uq_ticket_voucher_uuid'), 'ticket_voucher', type_='unique')
    op.drop_table('consent_withdrawal_code')
    # ### end Alembic commands ###
