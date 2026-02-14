from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import Base


class ConfiguracionAI(Base):
    __tablename__ = "configuracion_ai"

    id = Column(Integer, primary_key=True, index=True)
    proveedor = Column(String, nullable=False, default="deepseek")
    api_key = Column(String, nullable=False)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
