import json
import logging
import re
import time
from datetime import datetime
from typing import Optional
import requests
from sqlalchemy.orm import Session
from app.models.auto import Auto
from app.models.marca import Marca
from app.models.modelo import Modelo
from app.models.pricing import MarketRawListing
from app.services.ai_client import deepseek_chat, AIConfigError

logger = logging.getLogger(__name__)

REQUEST_DELAY = 1.2

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
    "Connection": "keep-alive",
}


def _slugify(text: str) -> str:
    return text.strip().lower().replace(".", "").replace(" ", "-")


def _build_source_urls(marca: str, modelo: str, anio: Optional[int]) -> dict:
    marca_slug = _slugify(marca)
    modelo_slug = _slugify(modelo)
    anio_q = str(anio) if anio else ""

    return {
        "infoauto": f"https://www.infoauto.com.ar/?s={marca}+{modelo}+{anio_q}",
        "acara": f"https://www.acara.org.ar/guia-oficial-de-precios/?s={marca}+{modelo}+{anio_q}",
        "deruedas": (
            "https://www.deruedas.com.ar/precio/Autos/Usados/Argentina"
            f"?segmento=0&marca={requests.utils.quote(marca)}&modelo={requests.utils.quote(modelo)}"
        ),
        "preciosdeautos": (
            "https://preciosdeautos.com.ar/anos_modelos/autos/"
            f"{marca_slug}/{modelo_slug}"
        ),
    }


def _fetch_html(url: str) -> Optional[str]:
    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        if response.status_code != 200:
            logger.warning("[AI] Status %s para %s", response.status_code, url)
            return None
        return response.text
    except requests.RequestException as exc:
        logger.error("[AI] Error de conexion %s", exc)
        return None


def _extract_json_list(content: str) -> list[dict]:
    try:
        data = json.loads(content)
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        pass

    match = re.search(r"\[[\s\S]*\]", content)
    if not match:
        return []

    try:
        data = json.loads(match.group(0))
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def _coerce_float(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    clean = re.sub(r"[^\d.]", "", str(value))
    try:
        return float(clean) if clean else None
    except ValueError:
        return None


def _coerce_int(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    clean = re.sub(r"[^\d]", "", str(value))
    try:
        return int(clean) if clean else None
    except ValueError:
        return None


def _normalize_item(item: dict, marca: str, modelo: str, source_url: str) -> dict:
    return {
        "titulo": item.get("titulo") or f"{marca} {modelo}",
        "marca_raw": item.get("marca_raw") or marca,
        "modelo_raw": item.get("modelo_raw") or modelo,
        "anio": _coerce_int(item.get("anio")),
        "km": _coerce_int(item.get("km")),
        "precio": _coerce_float(item.get("precio")),
        "moneda": (item.get("moneda") or "ARS").upper(),
        "ubicacion": item.get("ubicacion") or "",
        "url": item.get("url") or source_url,
    }


def _prompt_extract_listings(source: str, url: str, html: str, marca: str, modelo: str, anio: Optional[int]) -> list[dict]:
    html_snippet = html[:12000]
    prompt = (
        "Extrae informacion de precios de autos desde el HTML dado. "
        "Devuelve un JSON array con hasta 8 items. Cada item debe tener: "
        "titulo, marca_raw, modelo_raw, anio, km, precio, moneda, ubicacion, url. "
        "Reglas: SOLO incluir items que tengan precio y anio (no null). "
        "Si no hay precios, devuelve un array vacio []. "
        "No incluyas texto fuera del JSON. "
        f"Fuente: {source}. URL: {url}. "
        f"Auto objetivo: {marca} {modelo} {anio or ''}. "
    )

    messages = [
        {"role": "system", "content": "Eres un extractor de datos de autos."},
        {"role": "user", "content": prompt + "\n\nHTML:\n" + html_snippet},
    ]

    content = deepseek_chat(messages, max_tokens=700)
    return _extract_json_list(content)


def scrape_ai_source(
    db: Session,
    marca: str,
    modelo: str,
    anio: Optional[int],
    source: str,
) -> dict:
    stats = {"nuevos": 0, "duplicados": 0, "errores": 0}
    urls = _build_source_urls(marca, modelo, anio)
    source_url = urls.get(source)
    if not source_url:
        stats["errores"] += 1
        return stats

    html = _fetch_html(source_url)
    if not html:
        stats["errores"] += 1
        return stats

    try:
        items = _prompt_extract_listings(source, source_url, html, marca, modelo, anio)
    except AIConfigError as exc:
        logger.error("[AI] %s", exc)
        stats["errores"] += 1
        return stats
    except Exception as exc:
        logger.error("[AI] Error procesando IA: %s", exc)
        stats["errores"] += 1
        return stats

    existing_urls = set(
        u for (u,) in db.query(MarketRawListing.url).filter(
            MarketRawListing.fuente == f"ai_{source}"
        ).all()
    )

    nuevos = []
    for item in items:
        normalized = _normalize_item(item, marca, modelo, source_url)
        if not normalized.get("precio") or not normalized.get("anio"):
            stats["errores"] += 1
            continue
        url = normalized.get("url")
        if url and url in existing_urls:
            stats["duplicados"] += 1
            continue

        nuevos.append(MarketRawListing(
            fuente=f"ai_{source}",
            url=url,
            titulo=normalized["titulo"],
            marca_raw=normalized["marca_raw"],
            modelo_raw=normalized["modelo_raw"],
            anio=normalized["anio"],
            km=normalized["km"],
            precio=normalized["precio"],
            moneda=normalized["moneda"],
            ubicacion=normalized["ubicacion"],
            imagen_url=None,
            activo=True,
            procesado=False,
            fecha_scraping=datetime.utcnow(),
        ))
        if url:
            existing_urls.add(url)
        stats["nuevos"] += 1

    if nuevos:
        db.add_all(nuevos)
        db.commit()

    return stats


def scrape_all_ai(
    db: Session,
    max_autos: int = 20,
    sources: Optional[list[str]] = None,
) -> dict:
    total_stats = {"nuevos": 0, "duplicados": 0, "errores": 0}
    fuentes = sources or ["infoauto", "acara", "deruedas", "preciosdeautos"]

    autos = db.query(Auto).filter(Auto.en_stock == True).all()
    if not autos:
        logger.warning("[AI] No hay autos en stock para scrapear")
        return total_stats

    marcas = {m.id: m.nombre for m in db.query(Marca).all()}
    modelos = {m.id: m.nombre for m in db.query(Modelo).all()}

    combos = []
    seen = set()
    for auto in autos:
        key = (auto.marca_id, auto.modelo_id, auto.anio)
        if key in seen:
            continue
        seen.add(key)
        combos.append(key)
        if len(combos) >= max_autos:
            break

    for marca_id, modelo_id, anio in combos:
        marca = marcas.get(marca_id, "")
        modelo = modelos.get(modelo_id, "")
        if not marca or not modelo:
            continue

        for fuente in fuentes:
            stats = scrape_ai_source(db, marca, modelo, anio, fuente)
            for k in total_stats:
                total_stats[k] += stats[k]
            time.sleep(REQUEST_DELAY)

    logger.info("[AI] Scraping total completado: %s", total_stats)
    return total_stats
