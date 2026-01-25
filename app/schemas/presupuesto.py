from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PresupuestoBase(BaseModel):
    auto_id: int
    precio_sugerido: float
    comentarios: Optional[str] = None
    estado: Optional[str] = "pendiente"

class PresupuestoCreate(PresupuestoBase):
    pass

class PresupuestoOut(PresupuestoBase):
    id: int
    fecha_creacion: datetime
    class Config:
        from_attributes = True
