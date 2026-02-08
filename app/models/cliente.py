from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime


class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    apellido = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    telefono = Column(String, nullable=True)
    ciudad = Column(String, nullable=True)
    direccion = Column(String, nullable=True)
    fuente = Column(String, nullable=True)  # web, referido, publicidad, etc.
    
    # Calificación automática
    score = Column(Integer, default=0)
    calificacion = Column(String, default="frio")  # frio, tibio, caliente
    
    # Estado del cliente
    estado = Column(String, default="nuevo")  # nuevo, contactado, calificado, cliente, perdido
    
    # Preferencias
    preferencias_contacto = Column(String, nullable=True)  # email, telefono, whatsapp
    presupuesto_min = Column(Integer, nullable=True)
    presupuesto_max = Column(Integer, nullable=True)
    tipo_vehiculo_interes = Column(String, nullable=True)
    
    # Metadata
    notas = Column(Text, nullable=True)
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ultimo_contacto = Column(DateTime, nullable=True)
    ip_registro = Column(String, nullable=True)
    ubicacion_geo = Column(String, nullable=True)

    # Relaciones
    oportunidades = relationship("Oportunidad", back_populates="cliente")
