from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ConfiguracionAIBase(BaseModel):
    proveedor: str = "deepseek"
    api_key: str
    activo: Optional[bool] = True


class ConfiguracionAICreate(ConfiguracionAIBase):
    pass


class ConfiguracionAIUpdate(BaseModel):
    proveedor: Optional[str] = None
    api_key: Optional[str] = None
    activo: Optional[bool] = None


class ConfiguracionAIOut(BaseModel):
    id: Optional[int] = None
    proveedor: str = "deepseek"
    activo: bool = True
    has_key: bool = False
    api_key_last4: Optional[str] = None
    source: str = "db"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
