"""
Simulador de Tiempo de Venta.
Estima cuántos días tomaría vender un auto a un precio dado,
basándose en datos históricos de ventas.
"""
import statistics
import logging
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.auto import Auto
from app.models.venta import Venta
from app.models.pricing import MarketListing
from app.services.pricing_engine import clasificar_competitividad

logger = logging.getLogger(__name__)

# Tiempo base promedio de venta en días (si no hay datos históricos)
DIAS_BASE_VENTA = 45
# Factor: por cada 1% más caro que el mercado, se agregan X días
DIAS_POR_PCT_SOBREPRECIO = 1.0  # Reducido de 2.5 para evitar valores extremos
# Factor: por cada 1% más barato, se reducen X días
DIAS_POR_PCT_DESCUENTO = 1.5
# Mínimo de días estimados
DIAS_MINIMO = 3


def _obtener_historico_ventas(
    db: Session,
    marca_id: int,
    modelo_id: int,
    anio: int,
    rango_anio: int = 2,
) -> list[dict]:
    """
    Obtiene ventas históricas de autos similares para calcular tiempos.
    Retorna lista de {precio_venta, dias_en_stock, fecha_venta}.
    """
    # Buscar ventas completadas de autos similares
    ventas = (
        db.query(Venta)
        .join(Auto, Venta.auto_vendido_id == Auto.id)
        .filter(
            Auto.marca_id == marca_id,
            Auto.modelo_id == modelo_id,
            Auto.anio >= anio - rango_anio,
            Auto.anio <= anio + rango_anio,
            Venta.estado == "completada",
        )
        .all()
    )

    resultados = []
    for venta in ventas:
        # Estimar días en stock: diferencia entre fecha_creacion del auto y fecha_venta
        dias = 0
        if venta.fecha_venta and venta.fecha_creacion:
            delta = venta.fecha_venta - venta.fecha_creacion
            dias = max(delta.days, 1)
        resultados.append({
            "precio_venta": venta.precio_venta,
            "dias_en_stock": dias if dias > 0 else DIAS_BASE_VENTA,
        })

    return resultados


def _estimar_dias_venta(
    precio_propuesto: float,
    precio_mercado: float,
    historico: list[dict],
) -> float:
    """
    Estima días de venta usando regla estadística simple:
    1. Si hay histórico: interpolación lineal precio → días
    2. Si no: modelo basado en desviación del precio de mercado
    """
    if historico and len(historico) >= 3:
        # Usar histórico: correlación simple precio → días
        precios = [h["precio_venta"] for h in historico]
        dias = [h["dias_en_stock"] for h in historico]

        # Interpolación lineal simple
        precio_promedio = statistics.mean(precios)
        dias_promedio = statistics.mean(dias)

        if precio_promedio > 0:
            # Por cada % de diferencia vs promedio histórico, ajustar días
            pct_diff = (precio_propuesto - precio_promedio) / precio_promedio
            # Limitar pct_diff para evitar valores extremos
            pct_diff = max(min(pct_diff, 2.0), -2.0)  # Máximo ±200%
            ajuste = pct_diff * dias_promedio * 0.8  # factor de sensibilidad
            dias_estimados = dias_promedio + ajuste
            return max(dias_estimados, DIAS_MINIMO)

    # Fallback: modelo basado en desviación del mercado
    if precio_mercado > 0:
        pct_diff = ((precio_propuesto - precio_mercado) / precio_mercado) * 100
        # Limitar pct_diff para evitar valores extremos
        pct_diff = max(min(pct_diff, 200), -200)  # Máximo ±200%

        if pct_diff > 0:
            # Más caro que mercado
            dias = DIAS_BASE_VENTA + (pct_diff * DIAS_POR_PCT_SOBREPRECIO)
        else:
            # Más barato que mercado
            dias = DIAS_BASE_VENTA + (pct_diff * DIAS_POR_PCT_DESCUENTO)

        return max(dias, DIAS_MINIMO)

    return DIAS_BASE_VENTA


def _estimar_probabilidad_30dias(dias_estimados: float) -> float:
    """Estima la probabilidad de vender en 30 días basada en días estimados."""
    if dias_estimados <= 0:
        return 100.0
    if dias_estimados <= 30:
        return round(min(100, (30 / dias_estimados) * 60), 1)
    else:
        return round(max(5, (30 / dias_estimados) * 60), 1)


def simular_venta(
    db: Session,
    auto_id: int,
    precio_propuesto: float,
) -> dict:
    """
    Simula el tiempo de venta para un auto a un precio dado.
    Retorna: {precio_propuesto, dias_estimados, probabilidad_venta_30dias, margen_estimado, competitividad}
    """
    auto = db.query(Auto).filter(Auto.id == auto_id).first()
    if not auto:
        return {"error": "Auto no encontrado"}

    # Obtener precio de mercado (mediana de comparables)
    comparables = (
        db.query(MarketListing)
        .filter(
            MarketListing.marca_id == auto.marca_id,
            MarketListing.modelo_id == auto.modelo_id,
            MarketListing.anio >= auto.anio - 1,
            MarketListing.anio <= auto.anio + 1,
            MarketListing.activo == True,
            MarketListing.precio > 0,
        )
        .all()
    )

    precios_mercado = [c.precio for c in comparables]
    precio_mercado = statistics.median(precios_mercado) if precios_mercado else 0

    # Obtener histórico de ventas similares
    historico = _obtener_historico_ventas(
        db, auto.marca_id, auto.modelo_id, auto.anio
    )

    # Estimar días y probabilidad
    dias = _estimar_dias_venta(precio_propuesto, precio_mercado, historico)
    probabilidad = _estimar_probabilidad_30dias(dias)
    competitividad = clasificar_competitividad(precio_propuesto, precio_mercado) if precio_mercado else "sin_datos"

    # Margen estimado (precio propuesto - 85% como costo estimado)
    precio_compra_est = auto.precio * 0.85
    margen = precio_propuesto - precio_compra_est

    return {
        "precio_propuesto": round(precio_propuesto, 2),
        "dias_estimados": round(dias, 1),
        "probabilidad_venta_30dias": probabilidad,
        "margen_estimado": round(margen, 2),
        "competitividad": competitividad,
    }


def simular_rango(
    db: Session,
    auto_id: int,
    precio_min: float,
    precio_max: float,
    steps: int = 10,
) -> list[dict]:
    """
    Genera múltiples simulaciones entre un rango de precios.
    Pensado para el slider del frontend.
    """
    if steps < 2:
        steps = 2
    if steps > 50:
        steps = 50

    incremento = (precio_max - precio_min) / (steps - 1)
    resultados = []

    for i in range(steps):
        precio = precio_min + (incremento * i)
        sim = simular_venta(db, auto_id, precio)
        resultados.append(sim)

    return resultados
