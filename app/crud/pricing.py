"""
CRUD para el módulo de Pricing Inteligente.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional
from app.models.pricing import MarketRawListing, MarketListing


def listar_raw_listings(
    db: Session,
    fuente: Optional[str] = None,
    procesado: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[MarketRawListing]:
    query = db.query(MarketRawListing)
    if fuente:
        query = query.filter(MarketRawListing.fuente == fuente)
    if procesado is not None:
        query = query.filter(MarketRawListing.procesado == procesado)
    return query.order_by(desc(MarketRawListing.fecha_scraping)).offset(skip).limit(limit).all()


def listar_market_listings(
    db: Session,
    marca_id: Optional[int] = None,
    modelo_id: Optional[int] = None,
    anio: Optional[int] = None,
    fuente: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[MarketListing]:
    query = db.query(MarketListing).filter(MarketListing.activo == True)
    if marca_id:
        query = query.filter(MarketListing.marca_id == marca_id)
    if modelo_id:
        query = query.filter(MarketListing.modelo_id == modelo_id)
    if anio:
        query = query.filter(MarketListing.anio == anio)
    if fuente:
        query = query.filter(MarketListing.fuente == fuente)
    return query.order_by(desc(MarketListing.fecha_scraping)).offset(skip).limit(limit).all()


def contar_listings(db: Session) -> dict:
    total_raw = db.query(func.count(MarketRawListing.id)).scalar() or 0
    total_norm = db.query(func.count(MarketListing.id)).scalar() or 0
    no_procesados = db.query(func.count(MarketRawListing.id)).filter(
        MarketRawListing.procesado == False
    ).scalar() or 0
    return {
        "total_raw": total_raw,
        "total_normalizados": total_norm,
        "pendientes_normalizar": no_procesados,
    }


def obtener_market_listing(db: Session, listing_id: int) -> Optional[MarketListing]:
    return db.query(MarketListing).filter(MarketListing.id == listing_id).first()


def eliminar_listings_fuente(db: Session, fuente: str) -> int:
    count = db.query(MarketRawListing).filter(MarketRawListing.fuente == fuente).delete()
    db.commit()
    return count
