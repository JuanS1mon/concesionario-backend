from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.schemas.auto import Auto

class CotizacionBase(BaseModel):
    nombre_usuario: str
    email: str
    telefono: Optional[str] = None
    auto_id: int
    mensaje: str
    estado: Optional[str] = "nuevo"
    ciudad: Optional[str] = None
    fuente: Optional[str] = None
    preferencias_contacto: Optional[str] = None
    ip: Optional[str] = None
    ubicacion: Optional[str] = None
    notas_admin: Optional[str] = None

class CotizacionCreate(CotizacionBase):
    pass

class CotizacionOut(CotizacionBase):
    id: int
    fecha_creacion: datetime
    score: int
    estado_oportunidad: str
    auto: Optional[Auto] = None
    class Config:
        from_attributes = True
