"""
Scraper directo de deRuedas Argentina.
Hace web scraping del sitio https://www.deruedas.com.ar/ parseando HTML.
No requiere credenciales — scraping directo del sitio público.
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

DERUEDAS_BASE_URL = "https://www.deruedas.com.ar"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
    "Connection": "keep-alive",
}

REQUEST_DELAY = 1.5  # segundos


def _build_search_url(marca: str = "", modelo: str = "", page: int = 1) -> str:
    """
    Construye la URL de búsqueda en deRuedas.
    Patrón: /precio/Autos/Usados/Argentina?segmento=0&marca={Marca}&modelo={Modelo}&pag={N}
    """
    url = f"{DERUEDAS_BASE_URL}/precio/Autos/Usados/Argentina?segmento=0"
    if marca:
        # deRuedas usa nombres capitalizados tal cual: Toyota, Ford, Volkswagen
        url += f"&marca={requests.utils.quote(marca)}"
    if modelo:
        url += f"&modelo={requests.utils.quote(modelo)}"
    if page > 1:
        url += f"&pag={page}"
    return url


def _parse_precio(text: str) -> Optional[float]:
    """Parsea un precio de texto: '$ 19.500.000' -> 19500000."""
    if not text:
        return None
    try:
        clean = text.strip().replace(".", "").replace(",", "")
        clean = re.sub(r"[^\d]", "", clean)
        return float(clean) if clean else None
    except (ValueError, TypeError):
        return None


def _parse_km(text: str) -> Optional[int]:
    """Parsea kilometraje de texto: '57000 Km' -> 57000."""
    if not text:
        return None
    try:
        clean = re.sub(r"[^\d]", "", text)
        return int(clean) if clean else None
    except (ValueError, TypeError):
        return None


def _parse_anio(text: str) -> Optional[int]:
    """Parsea año de texto: '2017' -> 2017."""
    if not text:
        return None
    try:
        match = re.search(r"\b(19|20)\d{2}\b", text.strip())
        if match:
            anio = int(match.group())
            if 1990 <= anio <= 2030:
                return anio
        return None
    except (ValueError, TypeError):
        return None


def _extract_listing_data(card_el, marca_hint: str = "", modelo_hint: str = "") -> dict:
    """
    Extrae datos de un listing individual de deRuedas.

    Estructura HTML observada de cada card/listing:
    - Link: <a href="/vendo/Marca/Modelo/Usado/Provincia?cod=XXXXX">
    - Título: texto descriptivo completo (ej: "Toyota Etios 1.5 5ptas XLS 4AT (L16)")
    - Precio: "$ 19.500.000"
    - Atributos: "Nafta  |  2017" y "57000 Km"
    - Ubicación: "Mendoza, Capital"
    - Imagen: <img src="...">
    """
    data = {
        "url": "", "titulo": "", "marca": "", "modelo": "",
        "anio": None, "km": None, "precio": None, "moneda": "ARS",
        "ubicacion": "", "imagen_url": "", "combustible": "",
    }

    # --- Link (href) ---
    link_el = card_el.find("a", href=True)
    if link_el:
        href = link_el["href"]
        if not href.startswith("http"):
            href = DERUEDAS_BASE_URL + href
        data["url"] = href.split("#")[0]

        # Extraer marca/modelo de la URL: /vendo/Toyota/Etios/...
        url_parts = href.split("/")
        try:
            vendo_idx = url_parts.index("vendo")
            if len(url_parts) > vendo_idx + 2:
                data["marca"] = requests.utils.unquote(url_parts[vendo_idx + 1])
                data["modelo"] = requests.utils.unquote(url_parts[vendo_idx + 2]).replace("-", " ")
        except (ValueError, IndexError):
            pass

    # --- Título ---
    # Los links con texto descriptivo largo son los títulos
    links = card_el.find_all("a")
    for a in links:
        text = a.get_text(strip=True)
        if text and len(text) > 10 and not text.startswith("$"):
            data["titulo"] = text
            break

    if not data["titulo"] and link_el:
        data["titulo"] = link_el.get_text(strip=True)

    # --- Precio ---
    full_text = card_el.get_text(" ", strip=True)
    precio_match = re.search(r"\$\s*([\d.]+(?:\.\d{3})*)", full_text)
    if precio_match:
        data["precio"] = _parse_precio(precio_match.group(1))

    # Si hay U$S o USD, es dólares
    if "U$S" in full_text or "USD" in full_text:
        data["moneda"] = "USD"

    # --- Año ---
    # Buscar patrón de 4 dígitos que sea año (1990-2030)
    anio_matches = re.findall(r"\b(19\d{2}|20[0-2]\d)\b", full_text)
    for am in anio_matches:
        candidate = int(am)
        if 1990 <= candidate <= 2030:
            data["anio"] = candidate
            break

    # --- Kilómetros ---
    km_match = re.search(r"([\d.]+)\s*[Kk][Mm]", full_text)
    if km_match:
        data["km"] = _parse_km(km_match.group(1))

    # --- Combustible ---
    for comb in ["Nafta", "Diesel", "GNC", "Eléctrico", "Híbrido"]:
        if comb.lower() in full_text.lower():
            data["combustible"] = comb
            break

    # --- Ubicación ---
    # Suele estar al final: "Mendoza, Capital" o "Buenos Aires, ..."
    # Extraer de la URL si es posible: /vendo/Marca/Modelo/Usado/Provincia
    if data["url"]:
        url_parts = data["url"].split("/")
        try:
            vendo_idx = url_parts.index("vendo")
            if len(url_parts) > vendo_idx + 4:
                provincia = requests.utils.unquote(url_parts[vendo_idx + 4]).split("?")[0]
                data["ubicacion"] = provincia
        except (ValueError, IndexError):
            pass

    # --- Imagen ---
    img_el = card_el.find("img")
    if img_el:
        img_src = img_el.get("data-src") or img_el.get("src") or ""
        if img_src and not img_src.startswith("data:"):
            if not img_src.startswith("http"):
                img_src = DERUEDAS_BASE_URL + img_src
            data["imagen_url"] = img_src

    # --- Fallbacks marca/modelo ---
    if not data["marca"] and marca_hint:
        data["marca"] = marca_hint
    if not data["modelo"] and modelo_hint:
        data["modelo"] = modelo_hint

    return data


def scrape_deruedas_web(
    db: Session,
    marca: str = "",
    modelo: str = "",
    limit: int = 50,
    page: int = 1,
) -> dict:
    """
    Scrape directo del sitio web de deRuedas.
    Parsea el HTML de los resultados de búsqueda.
    Retorna dict con stats: {nuevos, duplicados, errores}.
    """
    stats = {"nuevos": 0, "duplicados": 0, "errores": 0}

    url = _build_search_url(marca, modelo, page)
    logger.info(f"[deRuedas] Scraping: {url}")

    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        if response.status_code != 200:
            logger.warning(f"[deRuedas] Status {response.status_code} para {url}")
            stats["errores"] += 1
            return stats
    except requests.RequestException as e:
        logger.error(f"[deRuedas] Error de conexión: {e}")
        stats["errores"] += 1
        return stats

    soup = BeautifulSoup(response.text, "html.parser")

    # Buscar todos los links de listings individuales: /vendo/Marca/Modelo/...
    # Cada listing es un bloque que contiene un link a /vendo/
    listing_links = soup.find_all("a", href=re.compile(r"/vendo/"))

    if not listing_links:
        logger.info(f"[deRuedas] 0 resultados para '{marca} {modelo}'")
        return stats

    # Agrupar: buscar el contenedor padre de cada link (evitar duplicados)
    # Estructura DOM: <div class="divCar_1"> → <div> (contenedor del listing)
    # El padre inmediato del link (Level 1) contiene los datos correctos
    seen_urls = set()
    cards = []
    for link in listing_links:
        href = link.get("href", "")
        if not href or "cod=" not in href:
            continue
        # Normalizar URL
        full_url = href if href.startswith("http") else DERUEDAS_BASE_URL + href
        clean_url = full_url.split("#")[0]

        if clean_url in seen_urls:
            continue
        seen_urls.add(clean_url)

        # El contenedor del listing está 1 nivel arriba del link
        # (div.divCar_1 → div contenedor con título/precio/atributos)
        card = link.parent
        if card and card.parent:
            card = card.parent
        cards.append(card or link)

    logger.info(f"[deRuedas] {len(cards)} listings encontrados para '{marca} {modelo}'")

    # Cargar URLs existentes en memoria
    existing_urls = set(
        u for (u,) in db.query(MarketRawListing.url).filter(
            MarketRawListing.fuente == "deruedas"
        ).all()
    )

    nuevos = []
    for card in cards[:limit]:
        try:
            data = _extract_listing_data(card, marca_hint=marca, modelo_hint=modelo)

            if not data["url"] or not data["precio"]:
                continue

            if data["url"] in existing_urls:
                stats["duplicados"] += 1
                continue

            nuevos.append(MarketRawListing(
                fuente="deruedas",
                url=data["url"],
                titulo=data["titulo"],
                marca_raw=data["marca"],
                modelo_raw=data["modelo"],
                anio=data["anio"],
                km=data["km"],
                precio=data["precio"],
                moneda=data["moneda"],
                ubicacion=data["ubicacion"],
                imagen_url=data["imagen_url"],
                activo=True,
                procesado=False,
                fecha_scraping=datetime.utcnow(),
            ))
            existing_urls.add(data["url"])
            stats["nuevos"] += 1

        except Exception as e:
            logger.error(f"[deRuedas] Error procesando listing: {e}")
            stats["errores"] += 1

    if nuevos:
        db.add_all(nuevos)
        db.commit()
        logger.info(f"[deRuedas] Guardados {len(nuevos)} nuevos listings")

    return stats


def scrape_all_deruedas(db: Session, max_por_marca: int = 50) -> dict:
    """
    Scrape automático de deRuedas: itera por todas las marcas/modelos
    registrados en el concesionario usando web scraping directo.
    Soporta paginación (recorre hasta 3 páginas por marca).
    """
    total_stats = {"nuevos": 0, "duplicados": 0, "errores": 0}
    MAX_PAGES = 3  # máximo de páginas a recorrer por búsqueda

    marcas = db.query(Marca).all()

    if not marcas:
        logger.warning("[deRuedas] No hay marcas registradas para scrapear")
        return total_stats

    for marca in marcas:
        listings_marca = 0
        for page in range(1, MAX_PAGES + 1):
            if listings_marca >= max_por_marca:
                break

            stats = scrape_deruedas_web(
                db, marca=marca.nombre,
                limit=max_por_marca - listings_marca,
                page=page,
            )
            for k in total_stats:
                total_stats[k] += stats[k]

            listings_marca += stats["nuevos"]

            # Si no encontramos nuevos en esta página, no tiene sentido seguir
            if stats["nuevos"] == 0 and stats["duplicados"] == 0:
                break

            time.sleep(REQUEST_DELAY)

    logger.info(f"[deRuedas] Scraping total completado: {total_stats}")
    return total_stats
