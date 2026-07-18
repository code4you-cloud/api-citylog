#from pydantic import BaseModel
#from typing import Optional
#
#class UserBase(BaseModel):
#    """Modello base per l'utente."""
#    email: Optional[str] = None
#    username: Optional[str] = None
#    facebook_id: Optional[str] = None
#    name: Optional[str] = None
#    avatar_url: Optional[str] = None
#
#class UserCreate(UserBase):
#    """Modello per la creazione di un nuovo utente."""
#    password: str
#
#class User(UserBase):
#    """Modello completo dell'utente (con campi dal DB)."""
#    id: int
#    is_active: bool
#
#    class Config:
#        #orm_mode = True
#        # Per Pydantic v2:
#        from_attributes = True
#
#

from pydantic import BaseModel, EmailStr
from typing import Optional, Union  #aggiungi questi import per facebook_id

class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    facebook_id: Optional[str] = None         #corretto per 3.9
    name: Optional[str] = None                #AGGIUNTO

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    facebook_id: Optional[str] = None         #corretto per 3,9

    class Config:
        from_attribute = True
        #orm_mode = True
