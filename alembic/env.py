from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

from app.db.database import Base
import app.models.citylog  # noqa - registra i model
import app.models.user     # noqa - registra i model

config = context.config
fileConfig(config.config_file_name)

target_metadata = Base.metadata

def include_object(object, name, type_, reflected, compare_to):
    # escludi tabelle non gestite da SQLAlchemy
    excluded_tables = {
        'auth_user', 'auth_group', 'auth_permission',
        'auth_user_groups', 'auth_user_user_permissions',
        'auth_group_permissions', 'django_migrations',
        'django_session', 'django_content_type', 'django_admin_log',
        'free_web', 'trees', 'api_keys'
    }
    if type_ == "table" and name in excluded_tables:
        return False
    return True

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        include_object=include_object,  # aggiungi questa riga
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,  #  aggiungi questa riga
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
