from sqlalchemy import Column, Integer, Float, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base
from datetime import datetime

class EmailData(Base):
    __tablename__ = "emails_emaildata"

    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(String, nullable=False)
    longitude = Column(String, nullable=False)
    city = Column(String, nullable=False)
    address = Column(Text, nullable=False)
    #image_time = Column(String, nullable=False)
    image_time = Column(DateTime, nullable=False, default=datetime.utcnow)  # Timestamp creazione
    image_id = Column(String, nullable=False)
    image_url = Column(String, nullable=False)
    image_file = Column(String, nullable=False)
    status = Column(String, nullable=False)
    typo = Column(String, nullable=False)  # Es. "rifiuti", "ambiente", "strade"
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Conferma nullable=True
    #user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    user = relationship("User", back_populates="emaildata")
