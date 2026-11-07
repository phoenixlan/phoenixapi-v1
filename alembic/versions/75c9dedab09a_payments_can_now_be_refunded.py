"""Payments can now be refunded

Revision ID: 75c9dedab09a
Revises: fe2e29d856d4
Create Date: 2026-11-07 12:20:40.903590

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '75c9dedab09a'
down_revision = 'fe2e29d856d4'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('payment', sa.Column('refunded_amount', sa.Integer(), server_default='0', nullable=False))

    # Alembic doesn't autogenerate enum value changes. ADD VALUE can't be used in the transaction that adds it
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE paymentstate ADD VALUE IF NOT EXISTS 'partially_refunded'")
        op.execute("ALTER TYPE paymentstate ADD VALUE IF NOT EXISTS 'refunded'")


def downgrade():
    op.drop_column('payment', 'refunded_amount')

    # Postgres can't drop an enum value, so recreate the type without them.
    # This fails if any refunded payments exist, which is intended - they can't be represented anymore
    op.execute("ALTER TYPE paymentstate RENAME TO paymentstate_old")
    op.execute("CREATE TYPE paymentstate AS ENUM ('created', 'initiated', 'paid', 'failed', 'tickets_minted')")
    op.execute("ALTER TABLE payment ALTER COLUMN state TYPE paymentstate USING state::text::paymentstate")
    op.execute("DROP TYPE paymentstate_old")
