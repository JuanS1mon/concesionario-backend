from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class Cotizacion(Base):
    __tablename__ = "cotizaciones"
    id = Column(Integer, primary_key=True, index=True)
    nombre_usuario = Column(String)
    email = Column(String)
    telefono = Column(String, nullable=True)
    auto_id = Column(Integer, ForeignKey("autos.id"))
    mensaje = Column(String)
    estado = Column(String, default="nuevo")
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    auto = relationship("Auto")
