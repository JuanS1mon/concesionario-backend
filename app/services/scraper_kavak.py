"""
Scraper directo de Kavak Argentina.
Extrae datos de autos del sitio https://www.kavak.com/ar/usados
parseando el JSON embebido en el HTML (React SSR).
No requiere credenciales.
"""
import requests
import logging
import json
import re
import time
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from app.models.pricing import MarketRawListing
from app.models.marca import Marca
from app.models.modelo import Modelo

logger = logging.getLogger(__name__)

KAVAK_BASE_URL = "https://www.kavak.com/ar/usados"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
    "Connection": "keep-alive",
}

REQUEST_DELAY = 1.5


def _build_kavak_url(marca: str = "", modelo: str = "", page: int = 1) -> str:
    """Construye la URL de búsqueda en Kavak."""
    url = KAVAK_BASE_URL
    if marca:
        slug = marca.lower().replace(" ", "-").replace(".", "")
        url += f"/{slug}"
        if modelo:
            modelo_slug = modelo.lower().replace(" ", "-").replace(".", "")
            url += f"-{modelo_slug}"
    if page > 1:
        sep = "?" if "?" not in url else "&"
        url += f"{sep}page={page}"
    return url


def _parse_precio_kavak(text: str) -> Optional[float]:
    """Parsea precio de Kavak: '15.940.000' -> 15940000."""
    if not text:
        return None
    try:
        clean = text.strip().replace(".", "").replace(",", "").replace("$", "").strip()
        return float(clean) if clean else None
    except (ValueError, TypeError):
        return None


def _extract_cars_from_html(html: str) -> list[dict]:
    """
    Extrae el array de autos del HTML de Kavak.
    Kavak usa React SSR y los datos están en un script con formato:
    \\"cars\\":[{\\"id\\":\\"...\\",...}]
    """
    # Buscar el marcador de cars con doble escape
    marker = '\\"cars\\":['
    start = html.find(marker)
    if start < 0:
        # Intentar sin doble escape (por si cambian el formato)
        marker = '"cars":['
        start = html.find(marker)
        if start < 0:
            return []

    idx = start + len(marker)
    bracket_count = 1
    i = idx
    while i < len(html) and bracket_count > 0:
        ch = html[i]
        if ch == '\\' and i + 1 < len(html):
            i += 2  # saltar carácter escapado
            continue
        if ch == '[':
            bracket_count += 1
        elif ch == ']':
            bracket_count -= 1
        i += 1

    raw = html[idx:i - 1]

    # Desescapar: \\" -> "  y \\/ -> /
    raw = raw.replace('\\"', '"').replace('\\/', '/')
    cars_json = '[' + raw + ']'

    try:
        return json.loads(cars_json)
    except json.JSONDecodeError as e:
        logger.error(f"[Kavak] Error parseando JSON de cars: {e}")
        return []


def _parse_car_data(car: dict) -> dict:
    """
    Parsea un objeto de auto de Kavak a nuestro formato.
    Campos disponibles: id, url, image, title, subtitle, mainPrice,
    footerInfo, analytics (car_make, car_model, car_price, car_location, car_id)
    """
    analytics = car.get("analytics", {})

    # Marca y modelo del analytics o del título
    marca = analytics.get("car_make", "")
    modelo = analytics.get("car_model", "")

    if not marca and car.get("title"):
        # Título formato: "Renault • Sandero"
        parts = car["title"].split("•")
        if len(parts) >= 2:
            marca = parts[0].strip()
            modelo = parts[1].strip()
        else:
            marca = car["title"].strip()

    # Año y KM del subtitle: "2017 • 49.500 km • 1.6 PRIVILEGE • Manual"
    subtitle = car.get("subtitle", "")
    anio = None
    km = None
    if subtitle:
        parts = [p.strip() for p in subtitle.split("•")]
        for p in parts:
            # Año
            if re.match(r"^\d{4}$", p):
                anio = int(p)
            # Kilómetros
            elif "km" in p.lower():
                km_clean = re.sub(r"[^\d]", "", p)
                if km_clean:
                    km = int(km_clean)

    # Precio
    precio_str = car.get("mainPrice", "")
    precio = _parse_precio_kavak(precio_str)
    if not precio and analytics.get("car_price"):
        try:
            precio = float(analytics["car_price"])
        except (ValueError, TypeError):
            pass

    # Ubicación
    ubicacion = car.get("footerInfo", analytics.get("car_location", ""))

    # URL
    url = car.get("url", "")
    if url and not url.startswith("http"):
        url = f"https://www.kavak.com{url}"

    # Imagen
    image = car.get("image", "")
    if image and not image.startswith("http"):
        image = f"https://images.kavak.services/{image}"

    return {
        "id": car.get("id", ""),
        "url": url,
        "titulo": f"{marca} {modelo} {anio or ''}".strip(),
        "marca": marca,
        "modelo": modelo,
        "anio": anio,
        "km": km,
        "precio": precio,
        "moneda": "ARS",
        "ubicacion": ubicacion,
        "imagen_url": image,
    }


def scrape_kavak_web(
    db: Session,
    marca: str = "",
    modelo: str = "",
    limit: int = 30,
    page: int = 1,
) -> dict:
    """
    Scrape directo del sitio web de Kavak.
    Extrae datos JSON embebidos en el HTML.
    Retorna dict con stats: {nuevos, duplicados, errores}.
    """
    stats = {"nuevos": 0, "duplicados": 0, "errores": 0}

    url = _build_kavak_url(marca, modelo, page)
    logger.info(f"[Kavak] Scraping: {url}")

    try:
        response = requests.get(url, headers=HEADERS, timeout=20, allow_redirects=True)
        if response.status_code != 200:
            logger.warning(f"[Kavak] Status {response.status_code} para {url}")
            stats["errores"] += 1
            return stats
    except requests.RequestException as e:
        logger.error(f"[Kavak] Error de conexión: {e}")
        stats["errores"] += 1
        return stats

    cars = _extract_cars_from_html(response.text)
    if not cars:
        logger.info(f"[Kavak] 0 resultados para '{marca} {modelo}'")
        return stats

    logger.info(f"[Kavak] {len(cars)} resultados para '{marca} {modelo}'")

    # Cargar URLs existentes
    existing_urls = set(
        u for (u,) in db.query(MarketRawListing.url).filter(
            MarketRawListing.fuente == "kavak"
        ).all()
    )

    nuevos = []
    for car_raw in cars[:limit]:
        try:
            car = _parse_car_data(car_raw)

            if not car["url"] or car["url"] in existing_urls:
                stats["duplicados"] += 1
                continue

            nuevos.append(MarketRawListing(
                fuente="kavak",
                url=car["url"],
                titulo=car["titulo"],
                marca_raw=car["marca"],
                modelo_raw=car["modelo"],
                anio=car["anio"],
                km=car["km"],
                precio=car["precio"],
                moneda=car["moneda"],
                ubicacion=car["ubicacion"],
                imagen_url=car["imagen_url"],
                activo=True,
                procesado=False,
                fecha_scraping=datetime.utcnow(),
            ))
            existing_urls.add(car["url"])
            stats["nuevos"] += 1

        except Exception as e:
            logger.error(f"[Kavak] Error procesando auto: {e}")
            stats["errores"] += 1

    if nuevos:
        db.add_all(nuevos)
        db.commit()
        logger.info(f"[Kavak] Guardados {len(nuevos)} nuevos listings")

    return stats


def scrape_all_kavak(db: Session, max_por_marca: int = 30) -> dict:
    """
    Scrape automático de Kavak: primero obtiene el catálogo general,
    luego busca por marcas específicas del concesionario.
    """
    total_stats = {"nuevos": 0, "duplicados": 0, "errores": 0}

    # 1. Primero scrapear la página general (tiene ~30 autos)
    stats = scrape_kavak_web(db, limit=30)
    for k in total_stats:
        total_stats[k] += stats[k]
    time.sleep(REQUEST_DELAY)

    # 2. Luego buscar por marcas del concesionario
    marcas = db.query(Marca).all()
    if not marcas:
        logger.warning("[Kavak] No hay marcas registradas para scrapear")
        return total_stats

    for marca in marcas:
        stats = scrape_kavak_web(db, marca=marca.nombre, limit=max_por_marca)
        for k in total_stats:
            total_stats[k] += stats[k]
        time.sleep(REQUEST_DELAY)

    logger.info(f"[Kavak] Scraping total completado: {total_stats}")
    return total_stats
