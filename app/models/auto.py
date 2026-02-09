from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

class Auto(Base):
    __tablename__ = "autos"
    id = Column(Integer, primary_key=True, index=True)
    marca_id = Column(Integer, ForeignKey("marcas.id"))
    modelo_id = Column(Integer, ForeignKey("modelos.id"))
    anio = Column(Integer)
    tipo = Column(String)
    precio = Column(Float)
    precio_compra = Column(Float, nullable=True)  # Precio al que se adquirió el auto
    es_trade_in = Column(Boolean, default=False)  # Si fue recibido como parte de un trade-in
    descripcion = Column(String)
    en_stock = Column(Boolean, default=True)
    estado_id = Column(Integer, ForeignKey("estados.id"))

    marca = relationship("Marca", back_populates="autos")
    modelo = relationship("Modelo", back_populates="autos")
    estado = relationship("Estado", back_populates="autos")
    imagenes = relationship("Imagen", back_populates="auto")
