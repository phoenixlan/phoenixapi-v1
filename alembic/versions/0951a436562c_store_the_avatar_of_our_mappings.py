"""Store the avatar of our mappings

Revision ID: 0951a436562c
Revises: 973632b0d6e9
Create Date: 2022-12-29 07:13:48.182627

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0951a436562c'
down_revision = '973632b0d6e9'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('discord_mapping', sa.Column('discord_avatar', sa.Text(), nullable=False))
    op.create_unique_constraint(op.f('uq_discord_mapping_oauth_state_code'), 'discord_mapping_oauth_state', ['code'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(op.f('uq_discord_mapping_oauth_state_code'), 'discord_mapping_oauth_state', type_='unique')
    op.drop_column('discord_mapping', 'discord_avatar')
    # ### end Alembic commands ###
