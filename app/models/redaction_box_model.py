# app/models/redaction_box_model.py  (minuscolo per convenzione file, la classe resta RedactionBoxModel)
from sqlalchemy import Column, BigInteger, String, Float, Boolean, ForeignKey
from app.db.database import Base


class RedactionBoxModel(Base):
    __tablename__ = "emails_redactionbox"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    box_type = Column(String(10), nullable=False)
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    w = Column(Float, nullable=False)
    h = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    confirmed = Column(Boolean, nullable=False)
    is_manual = Column(Boolean, nullable=False)
    report_id = Column(BigInteger, ForeignKey("emails_emaildata.id"), nullable=False)
