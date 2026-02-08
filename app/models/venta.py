from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime


class Venta(Base):
    __tablename__ = "ventas"

    id = Column(Integer, primary_key=True, index=True)

    # Cliente que compra
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)

    # Auto que se vende (sale del stock)
    auto_vendido_id = Column(Integer, ForeignKey("autos.id"), nullable=False)
    precio_venta = Column(Float, nullable=False)

    # Auto que el cliente entrega (entra al stock como No Disponible)
    auto_tomado_id = Column(Integer, ForeignKey("autos.id"), nullable=True)
    precio_toma = Column(Float, nullable=True)

    # Parte de pago y cálculos
    es_parte_pago = Column(Boolean, default=False)
    diferencia = Column(Float, nullable=True)  # precio_venta - precio_toma
    ganancia_estimada = Column(Float, nullable=True)

    # Vínculos opcionales con cotización/oportunidad
    cotizacion_id = Column(Integer, ForeignKey("cotizaciones.id"), nullable=True)
    oportunidad_id = Column(Integer, ForeignKey("oportunidades.id"), nullable=True)

    # Estado de la venta
    estado = Column(String, default="completada")  # pendiente, completada, cancelada

    # Notas
    notas = Column(Text, nullable=True)

    # Metadata
    fecha_venta = Column(DateTime, default=datetime.utcnow)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones ORM
    cliente = relationship("Cliente", foreign_keys=[cliente_id])
    auto_vendido = relationship("Auto", foreign_keys=[auto_vendido_id])
    auto_tomado = relationship("Auto", foreign_keys=[auto_tomado_id])
    cotizacion = relationship("Cotizacion", foreign_keys=[cotizacion_id])
    oportunidad = relationship("Oportunidad", foreign_keys=[oportunidad_id])
