# alembic/env.py — top of file
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import app.models.user
import app.models.Organization
import app.models.Role
import app.models.UserOrganizations
import app.models.Cluster
import app.models.Deployment

from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool

from app.models.base import Base  

config = context.config
fileConfig(config.config_file_name)
target_metadata = Base.metadata


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
