from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class EmailDataBase(BaseModel):
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    image_id: Optional[str] = None
    image_url: Optional[str] = None
    image_file: Optional[str] = None
    status: Optional[str] = None
    typo: Optional[str] = None # Es. "rifiuti", "ambiente", "strade"
    id: Optional[int] = None
    image_time: Optional[str] = None
    user_id: Optional[int] = None

class EmailDataCreate(EmailDataBase):
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    image_id: Optional[str] = None
    image_url: Optional[str] = None
    image_file: Optional[str] = None
    status: Optional[str] = None
    #pass

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

class SegnalazioneStatusUpdate(BaseModel):
    status: Optional[str] = None

class EmailData(EmailDataBase):
    id: int
    image_time: datetime
    user_id: Optional[int] = None

    class Config:
        from_attributes = True

class EmailDataPublic(BaseModel):
    id: int
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    image_time: Optional[datetime] = None
    status: Optional[str] = None

    class Config:
        from_attributes = True

class SegnalazioneOut(EmailDataBase):
    id: int
    image_time: datetime
    user_id: int

    class Config:
        from_attributes = True

class FacebookAuthRequest(BaseModel):
    access_token: str

    class Config:
        from_attributes = True
