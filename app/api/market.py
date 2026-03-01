"""
Endpoints públicos para consultas de mercado (usable por la app móvil sin login).
"""
from fastapi import APIRouter, Query, HTTPException, Depends, Response
import statistics
from sqlalchemy.orm import Session
from typing import Optional, List

from app.database import get_db
from app.models.pricing import MarketListing
from app.schemas.pricing import MarketListingOut
from app.services.pricing_engine import _trimmed_mean
from app.services.ai_client import deepseek_chat, get_deepseek_api_key
from app.database import SessionLocal
from app.models.pricing import MarketListing
from app.schemas.pricing import MarketListingOut

router = APIRouter(prefix="/market", tags=["market"])


import logging

@router.get("/search", response_model=List[MarketListingOut])
def search_market(
    marca_id: Optional[int] = Query(None),
    modelo_id: Optional[int] = Query(None),
    anio_min: Optional[int] = Query(None),
    anio_max: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Busca listings activos en el mercado filtrando por rango de años.
    Devuelve los resultados más recientes primero.
    """
    try:
        logging.info(f"/market/search params: marca_id={marca_id}, modelo_id={modelo_id}, anio_min={anio_min}, anio_max={anio_max}, skip={skip}, limit={limit}")
        query = db.query(MarketListing).filter(MarketListing.activo == True, MarketListing.precio > 0)
        if marca_id:
            query = query.filter(MarketListing.marca_id == marca_id)
        if modelo_id:
            query = query.filter(MarketListing.modelo_id == modelo_id)
        if anio_min is not None:
            query = query.filter(MarketListing.anio >= anio_min)
        if anio_max is not None:
            query = query.filter(MarketListing.anio <= anio_max)

        results = query.order_by(MarketListing.fecha_scraping.desc()).offset(skip).limit(limit).all()
        logging.info(f"/market/search results count: {len(results)}")
        # Log los resultados para debug (solo los ids y urls para no saturar)
        for r in results:
            logging.info(f"Result: id={r.id}, precio={r.precio}, url={r.url}")
        return results
    except Exception as e:
        logging.exception("Error en /market/search:")
        raise HTTPException(status_code=500, detail=f"Error interno en /market/search: {e}")


@router.get("/historico")
def market_historico(
    marca_id: Optional[int] = Query(None),
    modelo_id: Optional[int] = Query(None),
    anio_min: Optional[int] = Query(None),
    anio_max: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """Retorna la evolución histórica por año con la media recortada (se elimina mínimo y máximo).
    Respuesta: list de objetos {anio: int, precio_promedio: float}
    """
    query = db.query(MarketListing).filter(MarketListing.activo == True, MarketListing.precio > 0)
    if marca_id:
        query = query.filter(MarketListing.marca_id == marca_id)
    if modelo_id:
        query = query.filter(MarketListing.modelo_id == modelo_id)
    if anio_min is not None:
        query = query.filter(MarketListing.anio >= anio_min)
    if anio_max is not None:
        query = query.filter(MarketListing.anio <= anio_max)

    listings = query.order_by(MarketListing.anio.asc()).all()
    if not listings:
        raise HTTPException(status_code=404, detail="No hay datos de mercado para esos filtros")

    buckets: dict[int, List[float]] = {}
    for l in listings:
        year = l.anio or 0
        if year <= 0:
            continue
        buckets.setdefault(year, []).append(float(l.precio))

    series = []
    for year in sorted(buckets.keys()):
        precios = buckets[year]
        precio_prom = _trimmed_mean(precios, trim_count=1)
        series.append({"anio": year, "precio_promedio": round(precio_prom, 2) if precio_prom is not None else None, "count": len(precios)})

    return series


@router.get("/ai_sugerir")
def market_ai_sugerir(
    marca_id: Optional[int] = Query(None),
    modelo_id: Optional[int] = Query(None),
    anio_min: Optional[int] = Query(None),
    anio_max: Optional[int] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    response: Response = None,
):
    """Genera una sugerencia usando IA basada en los listings filtrados.
    Retorna texto de sugerencia y los `limit` mejores candidates.
    """
    try:
        # obtener comparables simples
        query = db.query(MarketListing).filter(MarketListing.activo == True, MarketListing.precio > 0)
        if marca_id:
            query = query.filter(MarketListing.marca_id == marca_id)
        if modelo_id:
            query = query.filter(MarketListing.modelo_id == modelo_id)
        if anio_min is not None:
            query = query.filter(MarketListing.anio >= anio_min)
        if anio_max is not None:
            query = query.filter(MarketListing.anio <= anio_max)

        listings = query.order_by(MarketListing.fecha_scraping.desc()).limit(200).all()
        if not listings:
            msg = "No hay datos de mercado para esos filtros. Prueba con otros valores."
            if response is not None:
                response.headers["Access-Control-Allow-Origin"] = "*"
            return {"sugerencia": msg, "candidates": []}

        precios = [float(l.precio) for l in listings if l.precio and l.precio > 0]
        if not precios:
            msg = "No hay precios válidos para esos filtros."
            if response is not None:
                response.headers["Access-Control-Allow-Origin"] = "*"
            return {"sugerencia": msg, "candidates": []}

        precio_trim = _trimmed_mean(precios, trim_count=1)
        mediana = statistics.median(precios)

        # seleccionar top candidates por cercanía a mediana
        def score(l: MarketListing):
            if not l.precio or mediana is None:
                return float('inf')
            return abs(float(l.precio) - mediana)

        candidates = sorted(listings, key=score)[:limit]

        # preparar prompt para la IA
        summary = {
            "count": len(precios),
            "mediana": mediana,
            "precio_trim": precio_trim,
        }

        # preparar datos de listings formateados
        listings_data = "\n".join([
            f"- {l.marca_id}/{l.modelo_id} {l.anio}: ${l.precio} ({l.km}km) - {l.url}"
            for l in candidates[:20]
        ])

        prompt = (
f"""
Actúa como asesor experto en autos usados.

Datos del mercado:
- Total listings: {summary['count']}
- Mediana: {summary['mediana']}
- Media recortada: {summary['precio_trim']}

LISTINGS:
{listings_data}

Tarea:
Selecciona los 5 mejores autos según:
- Precio competitivo vs mediana
- Buen balance año/kilometraje
- Descripción clara e historial verificable
- Mejor relación valor/precio

IMPORTANTE:

- NO escribas "Análisis", "Estrategia", "Factores" ni títulos.
- NO expliques el mercado.
- NO hagas introducciones.
- NO uses formato markdown en negrita.
- SOLO entrega la lista final de autos recomendados.

Formato obligatorio:

De acuerdo a lo analizado, te recomiendo estos autos:

1) Marca Modelo Año – Precio  
Motivo: explicación breve y concreta.  
Link: URL

(repetir para los 5 autos)

Máximo 10 líneas.
Sé directo.
"""
        )

        # llamar IA si está configurada
        api_key, _src = get_deepseek_api_key(db)
        sugerencia_text = None
        if api_key:
            messages = [
                {"role": "system", "content": "Eres un experto en compra/venta de autos usados."},
                {"role": "user", "content": prompt},
            ]
            try:
                sugerencia_text = deepseek_chat(messages, db=db)
            except Exception as e:
                sugerencia_text = f"IA no disponible: {e}"
        else:
            sugerencia_text = "IA no configurada en el servidor."

        # convertir candidates a dict serializable
        candidates_out = [
            {
                "id": c.id,
                "fuente": c.fuente,
                "marca_id": c.marca_id,
                "modelo_id": c.modelo_id,
                "anio": c.anio,
                "km": c.km,
                "precio": c.precio,
                "moneda": c.moneda,
                "url": c.url,
            }
            for c in candidates
        ]

        # fallback: asegurar header CORS si por alguna razón el middleware no se aplica
        if response is not None:
            response.headers["Access-Control-Allow-Origin"] = "*"
        return {"sugerencia": sugerencia_text, "candidates": candidates_out}
    except Exception as e:
        # Captura cualquier error y lo devuelve en sugerencia
        if response is not None:
            response.headers["Access-Control-Allow-Origin"] = "*"
        return {"sugerencia": f"Error interno: {e}", "candidates": []}
