from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=True)
    username = Column(String)
    name = Column(String)
    is_active = Column(Boolean, default=True)

    emaildata = relationship("EmailData", back_populates="user")
    # Aggiungi questi campi per social login
    facebook_id = Column(String(50), unique=True, index=True, nullable=True)
    # Opzionale: per futuri provider
    # google_id = Column(String(50), unique=True, index=True, nullable=True)
