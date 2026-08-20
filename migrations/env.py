from __future__ import annotations

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ------------------------------------------------------------
# Ensure project root is on sys.path so "pms_app" can be imported.
# migrations/..  => project root (where app.py is)
# ------------------------------------------------------------
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# ------------------------------------------------------------
# Import app db + models so metadata is populated
# ------------------------------------------------------------
from pms_app.extensions import db  # noqa: E402
import pms_app.models  # noqa: F401, E402

# Provide MetaData object for Alembic autogenerate
target_metadata = getattr(db, "metadata", None)

if target_metadata is None:
    raise RuntimeError(
        "env.py: target_metadata is None. "
        "Check pms_app/extensions.py to ensure db = SQLAlchemy() is defined."
    )


def _is_sqlite_url(url: str | None) -> bool:
    return bool(url) and url.strip().lower().startswith("sqlite")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    if not url:
        raise RuntimeError("sqlalchemy.url is empty. Set it in alembic.ini")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        # Helpful for SQLite schema changes (ALTER TABLE limitations)
        render_as_batch=_is_sqlite_url(url),
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        url = str(connection.engine.url)

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            render_as_batch=_is_sqlite_url(url),
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()