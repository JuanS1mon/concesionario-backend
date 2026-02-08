from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.schemas.auto import Auto


class OportunidadBase(BaseModel):
    cliente_id: int
    auto_id: Optional[int] = None
    titulo: str
    descripcion: Optional[str] = None
    etapa: Optional[str] = "prospecto"
    probabilidad: Optional[int] = 10
    valor_estimado: Optional[float] = None
    prioridad: Optional[str] = "media"
    notas: Optional[str] = None
    proxima_accion: Optional[str] = None
    fecha_proxima_accion: Optional[datetime] = None


class OportunidadCreate(OportunidadBase):
    pass


class OportunidadUpdate(BaseModel):
    cliente_id: Optional[int] = None
    auto_id: Optional[int] = None
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    etapa: Optional[str] = None
    probabilidad: Optional[int] = None
    valor_estimado: Optional[float] = None
    prioridad: Optional[str] = None
    motivo_perdida: Optional[str] = None
    notas: Optional[str] = None
    proxima_accion: Optional[str] = None
    fecha_proxima_accion: Optional[datetime] = None
    fecha_cierre: Optional[datetime] = None


class ClienteResumen(BaseModel):
    id: int
    nombre: str
    apellido: str
    email: str
    telefono: Optional[str] = None
    calificacion: str

    class Config:
        from_attributes = True


class OportunidadOut(OportunidadBase):
    id: int
    motivo_perdida: Optional[str] = None
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    fecha_cierre: Optional[datetime] = None
    cliente: Optional[ClienteResumen] = None
    auto: Optional[Auto] = None

    class Config:
        from_attributes = True
