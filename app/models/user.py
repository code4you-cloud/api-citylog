from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String)
    email = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)
    hashed_password = Column(String, nullable=True)
    api_key = Column(String)
    can_regenerate_key = Column(String)
    api_key_creation_date = Column(DateTime, nullable=True)

    emaildata = relationship("EmailData", back_populates="user")
    # Aggiungi questi campi per social login
    facebook_id = Column(String(50), unique=True, index=True, nullable=True)
    name = Column(String)
    # Opzionale: per futuri provider
    google_id = Column(String(50), unique=True, index=True, nullable=True)
    avatar_url = Column(String(255), nullable=True)  # Aggiungi questa riga
