from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ClienteBase(BaseModel):
    nombre: str
    apellido: str
    email: str
    telefono: Optional[str] = None
    ciudad: Optional[str] = None
    direccion: Optional[str] = None
    fuente: Optional[str] = None
    preferencias_contacto: Optional[str] = None
    presupuesto_min: Optional[int] = None
    presupuesto_max: Optional[int] = None
    tipo_vehiculo_interes: Optional[str] = None
    notas: Optional[str] = None


class ClienteCreate(ClienteBase):
    pass


class ClienteUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    ciudad: Optional[str] = None
    direccion: Optional[str] = None
    fuente: Optional[str] = None
    preferencias_contacto: Optional[str] = None
    presupuesto_min: Optional[int] = None
    presupuesto_max: Optional[int] = None
    tipo_vehiculo_interes: Optional[str] = None
    notas: Optional[str] = None
    estado: Optional[str] = None
    activo: Optional[bool] = None
    calificacion: Optional[str] = None


class ClienteOut(ClienteBase):
    id: int
    score: int
    calificacion: str
    estado: str
    activo: bool
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    ultimo_contacto: Optional[datetime] = None
    ip_registro: Optional[str] = None
    ubicacion_geo: Optional[str] = None
    total_oportunidades: Optional[int] = 0

    class Config:
        from_attributes = True
