from pydantic import BaseModel
from typing import Optional

class ModeloBase(BaseModel):
    nombre: str
    marca_id: int

class ModeloCreate(ModeloBase):
    pass

class ModeloUpdate(BaseModel):
    nombre: Optional[str] = None
    marca_id: Optional[int] = None

class Modelo(ModeloBase):
    id: int
    class Config:
        from_attributes = True
