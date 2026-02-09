from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime


class MarketRawListing(Base):
    """Datos crudos obtenidos del scraping de portales externos."""
    __tablename__ = "market_raw_listings"

    id = Column(Integer, primary_key=True, index=True)
    fuente = Column(String, nullable=False)  # mercadolibre, kavak
    url = Column(String, nullable=True, unique=True)
    titulo = Column(String, nullable=True)
    marca_raw = Column(String, nullable=True)
    modelo_raw = Column(String, nullable=True)
    anio = Column(Integer, nullable=True)
    km = Column(Integer, nullable=True)
    precio = Column(Float, nullable=True)
    moneda = Column(String, default="ARS")
    ubicacion = Column(String, nullable=True)
    imagen_url = Column(String, nullable=True)
    activo = Column(Boolean, default=True)
    procesado = Column(Boolean, default=False)
    fecha_publicacion = Column(DateTime, nullable=True)
    fecha_scraping = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('ix_market_raw_fuente', 'fuente'),
        Index('ix_market_raw_marca_modelo', 'marca_raw', 'modelo_raw'),
    )


class MarketListing(Base):
    """Datos normalizados de mercado, vinculados a marcas/modelos internos."""
    __tablename__ = "market_listings"

    id = Column(Integer, primary_key=True, index=True)
    raw_listing_id = Column(Integer, ForeignKey("market_raw_listings.id"), nullable=True)
    fuente = Column(String, nullable=False)
    marca_id = Column(Integer, ForeignKey("marcas.id"), nullable=False)
    modelo_id = Column(Integer, ForeignKey("modelos.id"), nullable=False)
    anio = Column(Integer, nullable=False)
    km = Column(Integer, nullable=True)
    precio = Column(Float, nullable=False)
    moneda = Column(String, default="ARS")
    ubicacion = Column(String, nullable=True)
    url = Column(String, nullable=True)
    activo = Column(Boolean, default=True)
    fecha_publicacion = Column(DateTime, nullable=True)
    fecha_scraping = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    marca = relationship("Marca", foreign_keys=[marca_id])
    modelo = relationship("Modelo", foreign_keys=[modelo_id])
    raw_listing = relationship("MarketRawListing", foreign_keys=[raw_listing_id])

    __table_args__ = (
        Index('ix_market_listings_comparables', 'marca_id', 'modelo_id', 'anio'),
        Index('ix_market_listings_fuente', 'fuente'),
    )
