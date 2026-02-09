"""
API endpoints para el módulo de Pricing Inteligente.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.api.deps import get_current_admin
from app.schemas.pricing import (
    PrecioSugerido,
    SimulacionRequest,
    SimulacionRangoRequest,
    SimulacionPrecio,
    EstadisticasPricing,
    ScrapingResult,
    NormalizacionResult,
    MarketListingOut,
    MarketRawListingOut,
)
from app.crud.pricing import listar_market_listings, listar_raw_listings, contar_listings
from app.services.pricing_engine import (
    calcular_precio_sugerido,
    analizar_inventario,
    obtener_comparables,
    obtener_estadisticas_pricing,
)
from app.services.simulador import simular_venta, simular_rango
from app.services.scraper_mercadolibre import scrape_all_mercadolibre
from app.services.scraper_kavak import scrape_all_kavak
from app.services.normalizer import normalizar_listings

router = APIRouter(prefix="/pricing", tags=["pricing"])


# ─── Análisis de inventario ────────────────────────────────────────

@router.get("/analisis", response_model=list[PrecioSugerido])
def analisis_inventario(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Analiza todos los autos en stock y genera precios sugeridos."""
    return analizar_inventario(db)


@router.get("/analisis/{auto_id}", response_model=PrecioSugerido)
def analisis_auto(
    auto_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Calcula el precio sugerido para un auto específico."""
    resultado = calcular_precio_sugerido(db, auto_id)
    if resultado.precio_actual == 0:
        raise HTTPException(status_code=404, detail="Auto no encontrado")
    return resultado


# ─── Comparables ───────────────────────────────────────────────────

@router.get("/comparables/{auto_id}", response_model=list[MarketListingOut])
def comparables_auto(
    auto_id: int,
    rango_anio: int = Query(1, ge=0, le=3),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Obtiene listings comparables del mercado para un auto."""
    from app.models.auto import Auto

    auto = db.query(Auto).filter(Auto.id == auto_id).first()
    if not auto:
        raise HTTPException(status_code=404, detail="Auto no encontrado")

    comparables = obtener_comparables(
        db, auto.marca_id, auto.modelo_id, auto.anio,
        rango_anio=rango_anio, limit=limit,
    )
    return comparables


# ─── Simulador ────────────────────────────────────────────────────

@router.post("/simular/{auto_id}", response_model=SimulacionPrecio)
def simular_precio(
    auto_id: int,
    request: SimulacionRequest,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Simula el tiempo de venta para un precio propuesto."""
    resultado = simular_venta(db, auto_id, request.precio_propuesto)
    if "error" in resultado:
        raise HTTPException(status_code=404, detail=resultado["error"])
    return resultado


@router.post("/simular-rango/{auto_id}", response_model=list[SimulacionPrecio])
def simular_rango_precios(
    auto_id: int,
    request: SimulacionRangoRequest,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Genera múltiples simulaciones para un rango de precios (slider)."""
    return simular_rango(
        db, auto_id,
        precio_min=request.precio_min,
        precio_max=request.precio_max,
        steps=request.steps,
    )


# ─── Estadísticas ────────────────────────────────────────────────

@router.get("/estadisticas", response_model=EstadisticasPricing)
def estadisticas_pricing(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Estadísticas globales del módulo de pricing."""
    return obtener_estadisticas_pricing(db)


# ─── Datos de mercado ────────────────────────────────────────────

@router.get("/mercado", response_model=list[MarketListingOut])
def listar_mercado(
    marca_id: Optional[int] = Query(None),
    modelo_id: Optional[int] = Query(None),
    anio: Optional[int] = Query(None),
    fuente: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Lista los datos de mercado normalizados."""
    return listar_market_listings(db, marca_id, modelo_id, anio, fuente, skip, limit)


@router.get("/mercado/raw", response_model=list[MarketRawListingOut])
def listar_raw(
    fuente: Optional[str] = Query(None),
    procesado: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Lista los datos crudos del scraping."""
    return listar_raw_listings(db, fuente, procesado, skip, limit)


# ─── Acciones de scraping / normalización ─────────────────────────

@router.post("/scrape", response_model=ScrapingResult)
def ejecutar_scraping(
    fuente: str = Query("all", pattern="^(mercadolibre|kavak|all)$"),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Ejecuta el scraping de datos de mercado."""
    total = {"nuevos": 0, "duplicados": 0, "errores": 0}

    if fuente in ("mercadolibre", "all"):
        stats_ml = scrape_all_mercadolibre(db)
        for k in total:
            total[k] += stats_ml[k]

    if fuente in ("kavak", "all"):
        stats_kv = scrape_all_kavak(db)
        for k in total:
            total[k] += stats_kv[k]

    return ScrapingResult(
        fuente=fuente,
        nuevos=total["nuevos"],
        duplicados=total["duplicados"],
        errores=total["errores"],
    )


@router.post("/normalizar", response_model=NormalizacionResult)
def ejecutar_normalizacion(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Normaliza los datos crudos del scraping."""
    stats = normalizar_listings(db)
    return NormalizacionResult(**stats)
