from __future__ import with_statement
from alembic import context
from sqlalchemy import engine_from_config, pool
from logging.config import fileConfig

import os

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
from phoenixRest.models import (
    Base,
    # TODO
)

from phoenixRest.models.core import (
    user,
    user_consent,
    event,
    avatar,
    agenda_entry,
    activation_code,
    password_reset_code,
    location
)

from phoenixRest.models.core.oauth import (
    oauthCode,
    refreshToken
)

from phoenixRest.models.crew import (
    crew,
    position,
    position_mapping,
    team,
    permission,
    application,
    application_crew_mapping
)

from phoenixRest.models.tickets import (
    entrance,
    row,
    seat,
    seatmap,
    ticket_type,
    store_session,
    store_session_cart_entry,
    payment,
    ticket,
    ticket_transfer,
    seatmap_background
)

from phoenixRest.models.tickets.payment_providers import (
    vipps_payment,
    stripe_payment
)

from phoenixRest.models.utils import (
    discord_mapping,
    discord_mapping_oauth_state
)


target_metadata = Base.metadata


# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    raise NotImplementedError("Currently broken")
    if "POSTGRES_USER" in os.environ and "POSTGRES_PASSWORD" in os.environ and "DB_HOST" in os.environ:
        print("Setting up postgresql connection url")
        connectionUri = "postgresql://%s:%s@%s/phoenix" % (os.environ['POSTGRES_USER'], os.environ['POSTGRES_PASSWORD'], os.environ['DB_HOST'])
        url = connectionUri
    else:
        print("No connection uri :(")
        url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    print("Alembic: running migrations online")
    section = config.get_section(config.config_ini_section)
    if "POSTGRES_USER" in os.environ and "POSTGRES_PASSWORD" in os.environ and "DB_HOST" in os.environ:
        print("Setting up postgresql connection url")
        connectionUri = "postgresql://%s:%s@%s/phoenix" % (os.environ['POSTGRES_USER'], os.environ['POSTGRES_PASSWORD'], os.environ['DB_HOST'])
        section['sqlalchemy.url'] = connectionUri

    connectable = engine_from_config(
        section,
        prefix='sqlalchemy.',
        poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
