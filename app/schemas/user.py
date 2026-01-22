from pydantic import BaseModel, EmailStr
from typing import Optional, Union  #aggiungi questi import per facebook_id

class UserBase(BaseModel):
    email: EmailStr
    username: str
    facebook_id: Optional[str] = None         #corretto per 3.9
    name: Optional[str] = None                #AGGIUNTO

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    facebook_id: Optional[str] = None         #corretto per 3,9

    class Config:
        orm_mode = True
