"""New payment provider type

Revision ID: 49c6ce337182
Revises: 4b2fd2e9ba9b
Create Date: 2026-09-27 06:00:06.834585

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '49c6ce337182'
down_revision = '4b2fd2e9ba9b'
branch_labels = None
depends_on = None


def upgrade():
    # Alembic doesn't autogenerate enum value changes. ADD VALUE can't be used in the transaction that adds it
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE paymentprovider ADD VALUE IF NOT EXISTS 'free'")


def downgrade():
    # Postgres can't drop an enum value, so recreate the type without it.
    # This fails if any free payments exist, which is intended - they can't be represented anymore
    op.execute("ALTER TYPE paymentprovider RENAME TO paymentprovider_old")
    op.execute("CREATE TYPE paymentprovider AS ENUM ('vipps', 'stripe')")
    op.execute("ALTER TABLE payment ALTER COLUMN provider TYPE paymentprovider USING provider::text::paymentprovider")
    op.execute("DROP TYPE paymentprovider_old")
