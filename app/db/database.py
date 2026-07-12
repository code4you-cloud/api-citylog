from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# sqlite connector
#SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"  # Modifica per il tuo DB

#engine = create_engine(
#    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
#)

# psql connector
# Configura l'URL del database PostgreSQL
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:postgres123@192.168.1.65:5432/geodumbmail_alembic"

# Crea il motore SQLAlchemy
engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
