from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class EmailDataBase(BaseModel):
    latitude: str
    longitude: str
    city: str
    address: str
    image_id: str
    image_url: str
    image_file: str
    status: str
    typo: str  # Es. "rifiuti", "ambiente", "strade"

class EmailDataCreate(EmailDataBase):
    pass

class EmailDataUpdate(BaseModel):  # Nuovo schema per PUT (aggiornamenti parziali)
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    image_id: Optional[str] = None
    image_url: Optional[str] = None
    image_file: Optional[str] = None
    status: Optional[str] = None
    typo: Optional[str] = None
    # Non includere typo, id, user_id, image_time (non modificabili)

class EmailData(EmailDataBase):
    id: int
    image_time: datetime
    user_id: Optional[int] = None

    class Config:
        from_attributes = True
