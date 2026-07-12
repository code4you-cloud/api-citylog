from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class QuartiereUpdateItem(BaseModel):
    id: Optional[int] = None
    image_id: Optional[str] = None
    latitudine: Optional[str] = None
    longitudine: Optional[str] = None
    typo: str
    quartiere: str

class QuartiereBatchUpdate(BaseModel):
    updates: List[QuartiereUpdateItem]
