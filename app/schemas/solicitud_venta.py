from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SolicitudVentaBase(BaseModel):
    nombre_interesado: str
    email: str
    telefono: Optional[str] = None
    auto_id: int
    mensaje: str
    estado: Optional[str] = "nuevo"

class SolicitudVentaCreate(SolicitudVentaBase):
    pass

class SolicitudVentaOut(SolicitudVentaBase):
    id: int
    fecha_creacion: datetime
    class Config:
        from_attributes = True
