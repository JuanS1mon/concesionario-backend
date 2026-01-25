from pydantic import BaseModel
from typing import Optional

class EstadoBase(BaseModel):
    nombre: str

class EstadoCreate(EstadoBase):
    pass

class EstadoUpdate(BaseModel):
    nombre: Optional[str] = None

class Estado(EstadoBase):
    id: int
    class Config:
        from_attributes = True
