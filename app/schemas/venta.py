from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.schemas.auto import Auto
from app.schemas.oportunidad import ClienteResumen


class AutoTomadoCreate(BaseModel):
    """Datos para crear el auto que el cliente entrega como parte de pago."""
    marca_id: int
    modelo_id: int
    anio: int
    tipo: str
    precio: float
    descripcion: Optional[str] = None


class VentaBase(BaseModel):
    cliente_id: int
    auto_vendido_id: int
    precio_venta: float
    precio_toma: Optional[float] = None
    es_parte_pago: Optional[bool] = False
    ganancia_estimada: Optional[float] = None
    cotizacion_id: Optional[int] = None
    oportunidad_id: Optional[int] = None
    estado: Optional[str] = "completada"
    notas: Optional[str] = None
    fecha_venta: Optional[datetime] = None


class VentaCreate(VentaBase):
    auto_tomado_data: Optional[AutoTomadoCreate] = None


class VentaUpdate(BaseModel):
    cliente_id: Optional[int] = None
    auto_vendido_id: Optional[int] = None
    precio_venta: Optional[float] = None
    precio_toma: Optional[float] = None
    es_parte_pago: Optional[bool] = None
    ganancia_estimada: Optional[float] = None
    cotizacion_id: Optional[int] = None
    oportunidad_id: Optional[int] = None
    estado: Optional[str] = None
    notas: Optional[str] = None
    fecha_venta: Optional[datetime] = None


class CotizacionResumen(BaseModel):
    id: int
    nombre_usuario: str
    email: str
    estado: str

    class Config:
        from_attributes = True


class OportunidadResumen(BaseModel):
    id: int
    titulo: str
    etapa: str
    valor_estimado: Optional[float] = None

    class Config:
        from_attributes = True


class VentaOut(VentaBase):
    id: int
    auto_tomado_id: Optional[int] = None
    diferencia: Optional[float] = None
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    cliente: Optional[ClienteResumen] = None
    auto_vendido: Optional[Auto] = None
    auto_tomado: Optional[Auto] = None
    cotizacion: Optional[CotizacionResumen] = None
    oportunidad: Optional[OportunidadResumen] = None

    class Config:
        from_attributes = True
