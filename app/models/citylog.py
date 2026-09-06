from sqlalchemy import BigInteger, Identity, Column, Integer, Float, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base
from datetime import datetime

class EmailData(Base):
    __tablename__ = "emails_emaildata"

    id = Column(BigInteger, Identity(), primary_key=True, index=True)
    latitude = Column(String(50), nullable=False)
    longitude = Column(String(50), nullable=False)
    city = Column(String(100), nullable=False)
    address = Column(Text, nullable=False)
    #image_time = Column(String, nullable=False)
    image_time = Column(DateTime, nullable=False, default=datetime.utcnow)  # Timestamp creazione
    image_id = Column(String(255), nullable=False)
    image_url = Column(String(255), nullable=False)
    image_file = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)
    typo = Column(String(20), nullable=False)  # Es. "rifiuti", "ambiente", "strade"
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Conferma nullable=True
    #user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status_int = Column(Integer, nullable=False)
    quartiere = Column(String(255), nullable=True)

    user = relationship("User", back_populates="emaildata")
    redacted_image = Column(String(255), nullable=True)
