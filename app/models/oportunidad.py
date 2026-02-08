from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime


class Oportunidad(Base):
    __tablename__ = "oportunidades"

    id = Column(Integer, primary_key=True, index=True)
    
    # Relaciones
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    auto_id = Column(Integer, ForeignKey("autos.id"), nullable=True)
    
    # Información de la oportunidad
    titulo = Column(String, nullable=False)
    descripcion = Column(Text, nullable=True)
    
    # Pipeline de ventas
    etapa = Column(String, default="prospecto")  # prospecto, contacto, evaluacion, negociacion, cierre, ganada, perdida
    probabilidad = Column(Integer, default=10)  # 0-100%
    valor_estimado = Column(Float, nullable=True)
    
    # Seguimiento
    prioridad = Column(String, default="media")  # baja, media, alta, urgente
    motivo_perdida = Column(String, nullable=True)
    
    # Tareas y notas
    notas = Column(Text, nullable=True)
    proxima_accion = Column(String, nullable=True)
    fecha_proxima_accion = Column(DateTime, nullable=True)
    
    # Metadata
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    fecha_cierre = Column(DateTime, nullable=True)

    # Relaciones ORM
    cliente = relationship("Cliente", back_populates="oportunidades")
    auto = relationship("Auto")
