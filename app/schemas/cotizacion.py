from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CotizacionBase(BaseModel):
    nombre_usuario: str
    email: str
    telefono: Optional[str] = None
    auto_id: int
    mensaje: str
    estado: Optional[str] = "nuevo"

class CotizacionCreate(CotizacionBase):
    pass

class CotizacionOut(CotizacionBase):
    id: int
    fecha_creacion: datetime
    class Config:
        from_attributes = True
