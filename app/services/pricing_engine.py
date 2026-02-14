"""
Motor de Pricing Inteligente.
Calcula precios sugeridos, competitividad y márgenes basándose en datos de mercado.
"""
import statistics
import logging
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.pricing import MarketListing, MarketRawListing
from app.models.auto import Auto
from app.schemas.pricing import PrecioSugerido, MarketListingOut

logger = logging.getLogger(__name__)

# Ajuste de precio por KM: se reduce $X por cada 10,000 km por encima del promedio
AJUSTE_POR_10K_KM = 50000  # ARS por cada 10k km extra (configurable)
KM_PROMEDIO_REFERENCIA = 50000  # km promedio de referencia


# Rangos progresivos de año para buscar comparables
RANGOS_ANIO_PROGRESIVOS = [1, 2, 3, 5, 8, 15]


def obtener_comparables(
    db: Session,
    marca_id: int,
    modelo_id: int,
    anio: int,
    rango_anio: int = 1,
    rango_km_pct: float = 0.3,
    km: Optional[int] = None,
    limit: int = 100,
    moneda: str = "ARS",
) -> list[MarketListing]:
    """
    Busca listings comparables en la base de datos de mercado.
    Filtra por marca, modelo, año ± rango, moneda, y opcionalmente km ± %.
    Si no encuentra resultados con rango pequeño, expande progresivamente.
    """
    def _query_comparables(rango: int) -> list[MarketListing]:
        query = db.query(MarketListing).filter(
            MarketListing.marca_id == marca_id,
            MarketListing.modelo_id == modelo_id,
            MarketListing.anio >= anio - rango,
            MarketListing.anio <= anio + rango,
            MarketListing.anio > 0,  # Excluir año=0 (datos inválidos)
            MarketListing.activo == True,
            MarketListing.precio > 0,
            MarketListing.moneda == moneda,
        )
        if km and rango_km_pct > 0:
            km_min = int(km * (1 - rango_km_pct))
            km_max = int(km * (1 + rango_km_pct))
            query = query.filter(
                MarketListing.km >= km_min,
                MarketListing.km <= km_max,
            )
        return query.limit(limit).all()

    # Intentar con rango progresivo hasta encontrar resultados
    for rango in RANGOS_ANIO_PROGRESIVOS:
        if rango < rango_anio:
            continue
        resultados = _query_comparables(rango)
        if resultados:
            if rango > rango_anio:
                logger.info(
                    f"[Pricing] Expandido rango año a ±{rango} para "
                    f"marca={marca_id} modelo={modelo_id} año={anio} → {len(resultados)} comparables"
                )
            return resultados

    # Si ARS no dio resultados, intentar con USD
    if moneda == "ARS":
        logger.info(f"[Pricing] Sin resultados en ARS, intentando USD")
        for rango in RANGOS_ANIO_PROGRESIVOS:
            resultados = _query_comparables_moneda(db, marca_id, modelo_id, anio, rango, km, rango_km_pct, "USD", limit)
            if resultados:
                return resultados

    # Último recurso: sin filtro de moneda ni año estricto
    query = db.query(MarketListing).filter(
        MarketListing.marca_id == marca_id,
        MarketListing.modelo_id == modelo_id,
        MarketListing.anio > 0,
        MarketListing.activo == True,
        MarketListing.precio > 0,
    ).order_by(
        func.abs(MarketListing.anio - anio)
    ).limit(limit)

    return query.all()


def _query_comparables_moneda(
    db: Session, marca_id: int, modelo_id: int, anio: int,
    rango: int, km: Optional[int], rango_km_pct: float,
    moneda: str, limit: int,
) -> list[MarketListing]:
    """Helper para buscar comparables con moneda específica."""
    query = db.query(MarketListing).filter(
        MarketListing.marca_id == marca_id,
        MarketListing.modelo_id == modelo_id,
        MarketListing.anio >= anio - rango,
        MarketListing.anio <= anio + rango,
        MarketListing.anio > 0,
        MarketListing.activo == True,
        MarketListing.precio > 0,
        MarketListing.moneda == moneda,
    )
    if km and rango_km_pct > 0:
        km_min = int(km * (1 - rango_km_pct))
        km_max = int(km * (1 + rango_km_pct))
        query = query.filter(
            MarketListing.km >= km_min,
            MarketListing.km <= km_max,
        )
    return query.limit(limit).all()


def _calcular_ajuste_km(km_auto: Optional[int], km_promedio_mercado: Optional[float]) -> float:
    """
    Calcula el ajuste de precio por kilometraje.
    Si el auto tiene más km que el promedio del mercado, se descuenta.
    Si tiene menos, se suma.
    """
    if km_auto is None or km_promedio_mercado is None:
        return 0.0
    diferencia_km = km_auto - km_promedio_mercado
    ajuste = (diferencia_km / 10000) * AJUSTE_POR_10K_KM
    return -ajuste  # negativo = descuento, positivo = premium


def clasificar_competitividad(precio_actual: float, precio_mercado: float) -> str:
    """
    Clasifica la competitividad del precio actual vs mercado.
    - muy_competitivo: precio < 95% del mercado
    - competitivo: precio entre 95% y 105% del mercado
    - caro: precio > 105% del mercado
    """
    if precio_mercado <= 0:
        return "sin_datos"
    ratio = precio_actual / precio_mercado
    if ratio < 0.95:
        return "muy_competitivo"
    elif ratio <= 1.05:
        return "competitivo"
    else:
        return "caro"


def calcular_precio_sugerido(db: Session, auto_id: int) -> PrecioSugerido:
    """
    Calcula el precio sugerido para un auto específico basándose en datos de mercado.
    """
    auto = db.query(Auto).filter(Auto.id == auto_id).first()
    if not auto:
        return PrecioSugerido(auto_id=auto_id, precio_actual=0)

    resultado = PrecioSugerido(
        auto_id=auto.id,
        marca=auto.marca.nombre if auto.marca else None,
        modelo=auto.modelo.nombre if auto.modelo else None,
        anio=auto.anio,
        precio_actual=auto.precio,
    )

    # Buscar comparables (intenta ARS primero, con rango progresivo)
    comparables = obtener_comparables(
        db, auto.marca_id, auto.modelo_id, auto.anio, moneda="ARS"
    )

    if not comparables:
        resultado.comparables_count = 0
        resultado.competitividad = "sin_datos"
        return resultado

    # Determinar moneda dominante de los comparables
    moneda_comparables = "ARS"
    monedas = [c.moneda for c in comparables]
    if monedas.count("USD") > monedas.count("ARS"):
        moneda_comparables = "USD"

    precios = [c.precio for c in comparables if c.precio > 0]
    if not precios:
        resultado.comparables_count = 0
        resultado.competitividad = "sin_datos"
        return resultado

    # Estadísticas de mercado
    promedio = statistics.mean(precios)
    mediana = statistics.median(precios)

    # Ajuste por km (si hay datos)
    kms_mercado = [c.km for c in comparables if c.km and c.km > 0]
    km_promedio = statistics.mean(kms_mercado) if kms_mercado else None
    ajuste_km = _calcular_ajuste_km(None, km_promedio)  # auto no tiene km field

    precio_sugerido = mediana + ajuste_km

    # Competitividad
    comp = clasificar_competitividad(auto.precio, mediana)

    # Cálculo de margen según origen del auto
    if auto.es_trade_in and auto.precio_compra:
        # Si fue trade-in, margen = precio_venta - precio_compra_del_cliente
        margen_actual = auto.precio - auto.precio_compra
        margen_sugerido = precio_sugerido - auto.precio_compra if precio_sugerido else None
    else:
        # Si no fue trade-in, margen = precio_venta - precio_minimo_mercado
        precio_minimo_mercado = min(precios) if precios else mediana
        margen_actual = auto.precio - precio_minimo_mercado
        margen_sugerido = precio_sugerido - precio_minimo_mercado if precio_sugerido else None

    # Convertir comparables a schema
    comparables_out = [
        MarketListingOut(
            id=c.id,
            fuente=c.fuente,
            marca_id=c.marca_id,
            modelo_id=c.modelo_id,
            anio=c.anio,
            km=c.km,
            precio=c.precio,
            moneda=c.moneda,
            ubicacion=c.ubicacion,
            url=c.url,
            activo=c.activo,
            fecha_scraping=c.fecha_scraping,
        )
        for c in comparables[:20]  # máximo 20 comparables en la respuesta
    ]

    resultado.precio_mercado_promedio = round(promedio, 2)
    resultado.precio_mercado_mediana = round(mediana, 2)
    resultado.precio_sugerido = round(precio_sugerido, 2)
    resultado.comparables_count = len(comparables)
    resultado.competitividad = comp
    resultado.margen_actual = round(margen_actual, 2) if margen_actual else None
    resultado.margen_sugerido = round(margen_sugerido, 2) if margen_sugerido else None
    resultado.ajuste_km = round(ajuste_km, 2) if ajuste_km else None
    resultado.comparables = comparables_out

    return resultado


def analizar_inventario(db: Session) -> list[PrecioSugerido]:
    """
    Analiza todos los autos en stock y genera precio sugerido para cada uno.
    """
    autos = db.query(Auto).filter(Auto.en_stock == True).all()
    resultados = []
    for auto in autos:
        resultado = calcular_precio_sugerido(db, auto.id)
        resultados.append(resultado)
    return resultados


def obtener_estadisticas_pricing(db: Session) -> dict:
    """
    Genera estadísticas globales del módulo de pricing.
    """
    autos_stock = db.query(Auto).filter(Auto.en_stock == True).all()
    total = len(autos_stock)

    con_datos = 0
    sin_datos = 0
    muy_comp = 0
    comp = 0
    caros = 0
    margenes = []

    for auto in autos_stock:
        comparables = obtener_comparables(
            db, auto.marca_id, auto.modelo_id, auto.anio
        )
        precios = [c.precio for c in comparables if c.precio > 0]

        if not precios:
            sin_datos += 1
            continue

        con_datos += 1
        mediana = statistics.median(precios)
        competitividad = clasificar_competitividad(auto.precio, mediana)

        if competitividad == "muy_competitivo":
            muy_comp += 1
        elif competitividad == "competitivo":
            comp += 1
        elif competitividad == "caro":
            caros += 1

        # Margen estimado
        margen = auto.precio - (auto.precio * 0.85)
        margenes.append(margen)

    total_listings = db.query(func.count(MarketListing.id)).scalar() or 0
    total_raw = db.query(func.count(MarketRawListing.id)).scalar() or 0

    fuentes = db.query(MarketListing.fuente).distinct().all()
    fuentes_activas = [f[0] for f in fuentes]

    return {
        "total_analizados": total,
        "con_datos_mercado": con_datos,
        "sin_datos_mercado": sin_datos,
        "muy_competitivos": muy_comp,
        "competitivos": comp,
        "caros": caros,
        "margen_promedio": round(statistics.mean(margenes), 2) if margenes else None,
        "precio_mercado_promedio_global": None,
        "total_listings_mercado": total_listings,
        "total_raw_listings": total_raw,
        "fuentes_activas": fuentes_activas,
    }
