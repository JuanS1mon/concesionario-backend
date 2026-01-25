from pydantic import BaseModel
from typing import Optional

class MarcaBase(BaseModel):
    nombre: str

class MarcaCreate(MarcaBase):
    pass

class MarcaUpdate(BaseModel):
    nombre: Optional[str] = None

class Marca(MarcaBase):
    id: int
    class Config:
        from_attributes = True
