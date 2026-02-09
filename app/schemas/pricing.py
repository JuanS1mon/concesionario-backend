from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# --- Market Listings ---

class MarketRawListingOut(BaseModel):
    id: int
    fuente: str
    url: Optional[str] = None
    titulo: Optional[str] = None
    marca_raw: Optional[str] = None
    modelo_raw: Optional[str] = None
    anio: Optional[int] = None
    km: Optional[int] = None
    precio: Optional[float] = None
    moneda: Optional[str] = "ARS"
    ubicacion: Optional[str] = None
    activo: bool
    procesado: bool
    fecha_scraping: datetime

    class Config:
        from_attributes = True


class MarketListingOut(BaseModel):
    id: int
    fuente: str
    marca_id: int
    modelo_id: int
    anio: int
    km: Optional[int] = None
    precio: float
    moneda: Optional[str] = "ARS"
    ubicacion: Optional[str] = None
    url: Optional[str] = None
    activo: bool
    fecha_scraping: datetime

    class Config:
        from_attributes = True


# --- Motor de Pricing ---

class PrecioSugerido(BaseModel):
    auto_id: int
    marca: Optional[str] = None
    modelo: Optional[str] = None
    anio: Optional[int] = None
    precio_actual: float
    precio_mercado_promedio: Optional[float] = None
    precio_mercado_mediana: Optional[float] = None
    precio_sugerido: Optional[float] = None
    comparables_count: int = 0
    competitividad: Optional[str] = None  # muy_competitivo, competitivo, caro
    margen_actual: Optional[float] = None
    margen_sugerido: Optional[float] = None
    ajuste_km: Optional[float] = None
    comparables: List[MarketListingOut] = []


class SimulacionPrecio(BaseModel):
    precio_propuesto: float
    dias_estimados: Optional[float] = None
    probabilidad_venta_30dias: Optional[float] = None
    margen_estimado: Optional[float] = None
    competitividad: Optional[str] = None


class SimulacionRangoRequest(BaseModel):
    precio_min: float
    precio_max: float
    steps: Optional[int] = 10


class SimulacionRequest(BaseModel):
    precio_propuesto: float


class EstadisticasPricing(BaseModel):
    total_analizados: int = 0
    con_datos_mercado: int = 0
    sin_datos_mercado: int = 0
    muy_competitivos: int = 0
    competitivos: int = 0
    caros: int = 0
    margen_promedio: Optional[float] = None
    precio_mercado_promedio_global: Optional[float] = None
    total_listings_mercado: int = 0
    total_raw_listings: int = 0
    fuentes_activas: List[str] = []


class ScrapingResult(BaseModel):
    fuente: str
    nuevos: int = 0
    duplicados: int = 0
    errores: int = 0
    mensaje: str = ""


class NormalizacionResult(BaseModel):
    procesados: int = 0
    normalizados: int = 0
    sin_match: int = 0
    outliers_filtrados: int = 0
    mensaje: str = ""
