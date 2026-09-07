from alembic import context
from backend.app.db import Base, engine
from backend.app import models

target_metadata = Base.metadata

if context.is_offline_mode():
    context.configure(
        url=engine.url, target_metadata=target_metadata,
        literal_binds=True, dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    from contextlib import nullcontext
    supplied = context.config.attributes.get("connection")
    with (nullcontext(supplied) if supplied is not None else engine.connect()) as connection:
        if connection.exec_driver_sql("SHOW server_encoding").scalar() != "UTF8":
            raise RuntimeError("Database must use UTF8 encoding")
        connection.rollback()
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
