"""
Scraper directo de MercadoLibre Argentina.
Hace web scraping del sitio https://autos.mercadolibre.com.ar/ parseando HTML.
No requiere credenciales de API — scraping directo del sitio público.
"""
import requests
import logging
import re
import time
from datetime import datetime
from typing import Optional
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from app.models.pricing import MarketRawListing
from app.models.marca import Marca
from app.models.modelo import Modelo

logger = logging.getLogger(__name__)

ML_BASE_URL = "https://autos.mercadolibre.com.ar"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
    "Connection": "keep-alive",
}

# Delay entre requests para ser respetuoso con el sitio
REQUEST_DELAY = 1.5  # segundos


def _build_search_url(marca: str, modelo: str = "", offset: int = 0) -> str:
    """Construye la URL de búsqueda de MercadoLibre Autos."""
    query = f"{marca} {modelo}".strip().lower().replace(" ", "-")
    url = f"{ML_BASE_URL}/{query}"
    if offset > 0:
        url += f"_Desde_{offset + 1}"
    return url


def _parse_precio(text: str) -> Optional[float]:
    """Parsea un precio de texto a número: '39.300.000' -> 39300000."""
    if not text:
        return None
    try:
        clean = text.strip().replace(".", "").replace(",", "").replace("$", "").replace("U$S", "").strip()
        return float(clean) if clean else None
    except (ValueError, TypeError):
        return None


def _parse_km(text: str) -> Optional[int]:
    """Parsea kilometraje de texto: '51.000 Km' -> 51000."""
    if not text:
        return None
    try:
        clean = re.sub(r"[^\d]", "", text)
        return int(clean) if clean else None
    except (ValueError, TypeError):
        return None


def _parse_anio(text: str) -> Optional[int]:
    """Parsea año de texto: '2022' -> 2022."""
    if not text:
        return None
    try:
        match = re.match(r"^\s*(\d{4})\s*$", text.strip())
        if match:
            anio = int(match.group(1))
            if 1990 <= anio <= 2030:
                return anio
        return None
    except (ValueError, TypeError):
        return None


def _extraer_marca_modelo_titulo(titulo: str) -> tuple[str, str]:
    """Extrae marca y modelo del título."""
    if not titulo:
        return "", ""
    partes = titulo.split()
    marca = partes[0] if partes else ""
    modelo = " ".join(partes[1:3]) if len(partes) > 1 else ""
    return marca, modelo


def scrape_mercadolibre_web(
    db: Session,
    marca: str = "",
    modelo: str = "",
    limit: int = 48,
    offset: int = 0,
) -> dict:
    """
    Scrape directo del sitio web de MercadoLibre.
    Parsea el HTML de los resultados de búsqueda.
    Retorna dict con stats: {nuevos, duplicados, errores}.
    """
    stats = {"nuevos": 0, "duplicados": 0, "errores": 0}

    if not marca:
        return stats

    url = _build_search_url(marca, modelo, offset)
    logger.info(f"[ML Web] Scraping: {url}")

    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        if response.status_code != 200:
            logger.warning(f"[ML Web] Status {response.status_code} para {url}")
            stats["errores"] += 1
            return stats
    except requests.RequestException as e:
        logger.error(f"[ML Web] Error de conexión: {e}")
        stats["errores"] += 1
        return stats

    soup = BeautifulSoup(response.text, "html.parser")
    items = soup.select("li.ui-search-layout__item")

    if not items:
        logger.info(f"[ML Web] 0 resultados para '{marca} {modelo}'")
        return stats

    logger.info(f"[ML Web] {len(items)} resultados para '{marca} {modelo}'")

    # Cargar URLs existentes en memoria
    existing_urls = set(
        u for (u,) in db.query(MarketRawListing.url).filter(
            MarketRawListing.fuente == "mercadolibre"
        ).all()
    )

    nuevos = []
    for item in items[:limit]:
        try:
            # --- Link ---
            link_el = item.select_one("a.ui-search-link") or item.select_one("a")
            href = link_el["href"] if link_el and link_el.get("href") else None
            if not href:
                continue
            url_clean = href.split("#")[0].split("?")[0]
            if not url_clean or url_clean in existing_urls:
                stats["duplicados"] += 1
                continue

            # --- Título ---
            title_el = (
                item.select_one(".ui-search-item__title")
                or item.select_one(".poly-component__title")
                or item.select_one("h2")
            )
            titulo = title_el.text.strip() if title_el else ""

            # --- Precio ---
            price_el = item.select_one(".andes-money-amount__fraction")
            precio = _parse_precio(price_el.text) if price_el else None

            # --- Moneda ---
            currency_el = item.select_one(".andes-money-amount__currency-symbol")
            moneda_text = currency_el.text.strip() if currency_el else "$"
            moneda = "USD" if "U$S" in moneda_text or "US" in moneda_text else "ARS"

            # --- Año y KM (desde atributos) ---
            attrs = item.select(".ui-search-card-attributes__attribute")
            if not attrs:
                attrs = item.select(".poly-component__attributes-list li")

            anio = None
            km = None
            for a in attrs:
                txt = a.text.strip()
                parsed_anio = _parse_anio(txt)
                if parsed_anio:
                    anio = parsed_anio
                elif "km" in txt.lower() or re.match(r"^[\d.]+\s", txt):
                    km = _parse_km(txt)

            # Fallback: extraer año del título
            if not anio:
                anio_match = re.search(r"\b(19|20)\d{2}\b", titulo)
                if anio_match:
                    anio = int(anio_match.group())

            # --- Marca / Modelo ---
            marca_raw, modelo_raw = _extraer_marca_modelo_titulo(titulo)
            if marca:
                marca_raw = marca
            if modelo:
                modelo_raw = modelo

            # --- Ubicación ---
            loc_el = (
                item.select_one(".ui-search-item__location")
                or item.select_one(".poly-component__location")
            )
            ubicacion = loc_el.text.strip() if loc_el else ""

            # --- Imagen ---
            img_el = (
                item.select_one("img.ui-search-result-image__element")
                or item.select_one("img")
            )
            img_src = ""
            if img_el:
                img_src = img_el.get("data-src") or img_el.get("src") or ""

            nuevos.append(MarketRawListing(
                fuente="mercadolibre",
                url=url_clean,
                titulo=titulo,
                marca_raw=marca_raw,
                modelo_raw=modelo_raw,
                anio=anio,
                km=km,
                precio=precio,
                moneda=moneda,
                ubicacion=ubicacion,
                imagen_url=img_src,
                activo=True,
                procesado=False,
                fecha_scraping=datetime.utcnow(),
            ))
            existing_urls.add(url_clean)
            stats["nuevos"] += 1

        except Exception as e:
            logger.error(f"[ML Web] Error procesando item: {e}")
            stats["errores"] += 1

    if nuevos:
        db.add_all(nuevos)
        db.commit()
        logger.info(f"[ML Web] Guardados {len(nuevos)} nuevos listings")

    return stats


def scrape_all_mercadolibre(db: Session, max_por_marca: int = 48) -> dict:
    """
    Scrape automático de MercadoLibre: itera por todas las marcas/modelos
    registrados en el concesionario usando web scraping directo.
    """
    total_stats = {"nuevos": 0, "duplicados": 0, "errores": 0}

    marcas = db.query(Marca).all()
    modelos = db.query(Modelo).all()

    if not marcas:
        logger.warning("[ML Web] No hay marcas registradas para scrapear")
        return total_stats

    modelos_por_marca: dict[int, list] = {}
    for m in modelos:
        modelos_por_marca.setdefault(m.marca_id, []).append(m)

    for marca in marcas:
        marca_modelos = modelos_por_marca.get(marca.id, [])

        if not marca_modelos:
            stats = scrape_mercadolibre_web(db, marca=marca.nombre, limit=max_por_marca)
            for k in total_stats:
                total_stats[k] += stats[k]
            time.sleep(REQUEST_DELAY)
        else:
            for modelo_obj in marca_modelos:
                stats = scrape_mercadolibre_web(
                    db, marca=marca.nombre, modelo=modelo_obj.nombre, limit=max_por_marca
                )
                for k in total_stats:
                    total_stats[k] += stats[k]
                time.sleep(REQUEST_DELAY)

    logger.info(f"[ML Web] Scraping total completado: {total_stats}")
    return total_stats
