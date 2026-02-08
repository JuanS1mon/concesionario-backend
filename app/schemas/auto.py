from pydantic import BaseModel
from typing import Optional, List
from app.schemas.marca import Marca
from app.schemas.modelo import Modelo
from app.schemas.estado import Estado

class ImagenOut(BaseModel):
    id: int
    url: str
    class Config:
        from_attributes = True

class AutoBase(BaseModel):
    marca_id: int
    modelo_id: int
    anio: int
    tipo: str
    precio: float
    descripcion: Optional[str] = None
    en_stock: Optional[bool] = True
    estado_id: int

class AutoCreate(AutoBase):
    pass

class AutoUpdate(BaseModel):
    marca_id: Optional[int] = None
    modelo_id: Optional[int] = None
    anio: Optional[int] = None
    tipo: Optional[str] = None
    precio: Optional[float] = None
    descripcion: Optional[str] = None
    en_stock: Optional[bool] = None
    estado_id: Optional[int] = None

class Auto(AutoBase):
    id: int
    imagenes: List[ImagenOut] = []
    marca: Optional[Marca] = None
    modelo: Optional[Modelo] = None
    estado: Optional[Estado] = None
    class Config:
        from_attributes = True
