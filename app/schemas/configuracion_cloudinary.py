from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ConfiguracionCloudinaryBase(BaseModel):
    cloud_name: str
    api_key: str
    api_secret: str
    upload_preset: str
    activo: Optional[bool] = True

class ConfiguracionCloudinaryCreate(ConfiguracionCloudinaryBase):
    pass

class ConfiguracionCloudinaryUpdate(BaseModel):
    cloud_name: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    upload_preset: Optional[str] = None
    activo: Optional[bool] = None

class ConfiguracionCloudinary(ConfiguracionCloudinaryBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True