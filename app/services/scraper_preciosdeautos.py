"""
Scraper de precios de referencia de PreciosDeAutos.com.ar.
Navega la estructura jerárquica del sitio:
  /marcas/autos → /autos/{marca} → /anos_modelos/autos/{marca}/{modelo}
Extrae precios de referencia por marca/modelo/año (no anuncios individuales).

Los datos se guardan como MarketRawListing con fuente="preciosdeautos"
y se normalizan igual que MercadoLibre/Kavak/deRuedas.
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

PDA_BASE_URL = "https://preciosdeautos.com.ar"

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


def _build_marca_url(marca: str) -> str:
    """Construye la URL de una marca: /autos/{marca-slug}"""
    slug = marca.lower().strip().replace(" ", "-").replace(".", "")
    return f"{PDA_BASE_URL}/autos/{slug}"


def _build_modelo_url(marca: str, modelo: str) -> str:
    """Construye la URL de un modelo: /anos_modelos/autos/{marca}/{modelo}"""
    marca_slug = marca.lower().strip().replace(" ", "-").replace(".", "")
    modelo_slug = modelo.lower().strip().replace(" ", "-").replace(".", "")
    return f"{PDA_BASE_URL}/anos_modelos/autos/{marca_slug}/{modelo_slug}"


def _parse_precio(text: str) -> Optional[float]:
    """Parsea un precio: '$ 19.500.000' -> 19500000."""
    if not text:
        return None
    try:
        clean = re.sub(r"[^\d]", "", text.strip())
        return float(clean) if clean else None
    except (ValueError, TypeError):
        return None


def _parse_rango_precios(text: str) -> tuple[Optional[float], Optional[float]]:
    """
    Parsea un rango de precios:
    '$ 10.148.500 ⟶ $ 13.238.700' -> (10148500.0, 13238700.0)
    '$ 36.104.000 ⟶ $ 46.636.000' -> (36104000.0, 46636000.0)
    """
    precios = re.findall(r"\$\s*([\d.]+(?:\.\d{3})*)", text)
    precio_min = _parse_precio(precios[0]) if len(precios) > 0 else None
    precio_max = _parse_precio(precios[1]) if len(precios) > 1 else None
    return precio_min, precio_max


def _get_modelos_from_marca_page(marca: str) -> list[dict]:
    """
    Obtiene la lista de modelos disponibles para una marca.
    Navega /autos/{marca} y extrae los links a modelos.
    Retorna lista de dicts: [{nombre, url}, ...]
    """
    url = _build_marca_url(marca)
    logger.debug(f"[PreciosDeAutos] Listando modelos: {url}")

    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        if response.status_code != 200:
            logger.warning(f"[PreciosDeAutos] Status {response.status_code} para {url}")
            return []
    except requests.RequestException as e:
        logger.error(f"[PreciosDeAutos] Error de conexión: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    modelos = []

    # Los modelos están en links tipo /anos_modelos/autos/{marca}/{modelo}
    for link in soup.find_all("a", href=re.compile(r"/anos_modelos/autos/")):
        href = link.get("href", "")
        # Extraer nombre del modelo del texto del link
        nombre = link.get_text(strip=True)
        # Limpiar: a veces incluye "Foto TOYOTA" como prefijo de un alt de imagen
        nombre = re.sub(r"^Foto\s+\w+\s*", "", nombre).strip()
        if nombre and href:
            full_url = href if href.startswith("http") else PDA_BASE_URL + href
            modelos.append({"nombre": nombre, "url": full_url})

    return modelos


def _scrape_modelo_precios(
    marca: str, modelo: str, modelo_url: str
) -> list[dict]:
    """
    Scrapea los precios por año de un modelo específico.
    Navega /anos_modelos/autos/{marca}/{modelo} y extrae la tabla de precios.
    Retorna lista de dicts: [{anio, precio_min, precio_max, versiones}, ...]
    """
    logger.debug(f"[PreciosDeAutos] Scraping precios: {modelo_url}")

    try:
        response = requests.get(modelo_url, headers=HEADERS, timeout=20)
        if response.status_code != 200:
            logger.warning(f"[PreciosDeAutos] Status {response.status_code} para {modelo_url}")
            return []
    except requests.RequestException as e:
        logger.error(f"[PreciosDeAutos] Error de conexión: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    resultados = []

    # La tabla tiene filas con: Año | Rango precios | Cant versiones
    # Buscar todas las filas de tabla o bloques con datos de año
    rows = soup.find_all("tr")
    if not rows:
        # Fallback: buscar divs o cualquier contenedor con datos tabulares
        rows = soup.find_all("div", class_=re.compile(r"row|item|card"))

    for row in rows:
        text = row.get_text(" ", strip=True)
        if not text:
            continue

        # Buscar año: "2023" o "0km"
        anio = None
        es_0km = False
        anio_match = re.search(r"\b(19\d{2}|20[0-2]\d)\b", text)
        if anio_match:
            anio = int(anio_match.group())
        elif "0km" in text.lower() or "0 km" in text.lower():
            es_0km = True
            anio = datetime.now().year  # Usar año actual para 0km

        if anio is None and not es_0km:
            continue

        # Buscar precios en la fila
        precio_min, precio_max = _parse_rango_precios(text)
        if not precio_min and not precio_max:
            continue

        # Cant de versiones (número solo)
        versiones_match = re.findall(r"\b(\d{1,3})\b", text)
        # Filtrar: las versiones suelen ser números < 100 que no son años ni precios
        versiones = None
        for v in versiones_match:
            num = int(v)
            if 1 <= num <= 100 and num != anio and num not in (0,):
                versiones = num
                break

        # Calcular precio promedio como referencia
        if precio_min and precio_max:
            precio_promedio = (precio_min + precio_max) / 2
        else:
            precio_promedio = precio_min or precio_max

        resultados.append({
            "marca": marca,
            "modelo": modelo,
            "anio": anio,
            "precio_min": precio_min,
            "precio_max": precio_max,
            "precio_promedio": precio_promedio,
            "versiones": versiones,
            "es_0km": es_0km,
            "url": modelo_url,
        })

    return resultados


def scrape_preciosdeautos(
    db: Session,
    marca: str,
    modelos_filtro: list[str] | None = None,
    limit: int = 50,
) -> dict:
    """
    Scrape de precios de referencia de PreciosDeAutos para una marca.
    Si modelos_filtro tiene valores, solo scrapea esos modelos.
    Retorna dict con stats: {nuevos, duplicados, errores}.
    """
    stats = {"nuevos": 0, "duplicados": 0, "errores": 0}

    # 1. Obtener lista de modelos disponibles en el sitio
    modelos_sitio = _get_modelos_from_marca_page(marca)
    if not modelos_sitio:
        logger.info(f"[PreciosDeAutos] No se encontraron modelos para '{marca}'")
        return stats

    logger.info(f"[PreciosDeAutos] {len(modelos_sitio)} modelos encontrados para '{marca}'")

    # Filtrar modelos si corresponde
    if modelos_filtro:
        filtro_lower = [m.lower() for m in modelos_filtro]
        modelos_sitio = [
            m for m in modelos_sitio
            if any(f in m["nombre"].lower() or m["nombre"].lower() in f for f in filtro_lower)
        ]

    # Cargar URLs existentes
    existing_keys = set(
        f"{r.marca_raw}|{r.modelo_raw}|{r.anio}"
        for r in db.query(MarketRawListing).filter(
            MarketRawListing.fuente == "preciosdeautos"
        ).all()
    )

    nuevos = []
    count = 0
    for modelo_info in modelos_sitio:
        if count >= limit:
            break

        time.sleep(REQUEST_DELAY)
        precios = _scrape_modelo_precios(marca, modelo_info["nombre"], modelo_info["url"])

        for p in precios:
            if count >= limit:
                break

            # Deduplicar por marca+modelo+año
            key = f"{p['marca']}|{p['modelo']}|{p['anio']}"
            if key in existing_keys:
                stats["duplicados"] += 1
                continue

            # Construir un título descriptivo
            titulo = f"{p['marca']} {p['modelo']} {p['anio']}"
            if p["es_0km"]:
                titulo += " 0km"
            if p["precio_min"] and p["precio_max"]:
                titulo += f" (${p['precio_min']:,.0f} - ${p['precio_max']:,.0f})"

            # URL única para deduplicación: modelo_url#anio
            url_unica = f"{p['url']}#{p['anio']}"

            nuevos.append(MarketRawListing(
                fuente="preciosdeautos",
                url=url_unica,
                titulo=titulo,
                marca_raw=p["marca"],
                modelo_raw=p["modelo"],
                anio=p["anio"],
                km=None,  # No aplica para precios de referencia
                precio=p["precio_promedio"],
                moneda="ARS",
                ubicacion="Nacional",  # Precios nacionales de referencia
                imagen_url="",
                activo=True,
                procesado=False,
                fecha_scraping=datetime.utcnow(),
            ))
            existing_keys.add(key)
            stats["nuevos"] += 1
            count += 1

    if nuevos:
        db.add_all(nuevos)
        db.commit()
        logger.info(f"[PreciosDeAutos] Guardados {len(nuevos)} nuevos registros de precios")

    return stats


def scrape_all_preciosdeautos(db: Session, max_por_marca: int = 50) -> dict:
    """
    Scrape automático de PreciosDeAutos: itera por todas las marcas
    registradas en el concesionario y obtiene precios de referencia.
    """
    total_stats = {"nuevos": 0, "duplicados": 0, "errores": 0}

    marcas = db.query(Marca).all()

    if not marcas:
        logger.warning("[PreciosDeAutos] No hay marcas registradas para scrapear")
        return total_stats

    # Obtener modelos del concesionario para filtrar
    modelos = db.query(Modelo).all()
    modelos_por_marca: dict[int, list[str]] = {}
    for m in modelos:
        modelos_por_marca.setdefault(m.marca_id, []).append(m.nombre)

    for marca in marcas:
        modelos_filtro = modelos_por_marca.get(marca.id, None)

        stats = scrape_preciosdeautos(
            db, marca=marca.nombre,
            modelos_filtro=modelos_filtro,
            limit=max_por_marca,
        )
        for k in total_stats:
            total_stats[k] += stats[k]

        time.sleep(REQUEST_DELAY)

    logger.info(f"[PreciosDeAutos] Scraping total completado: {total_stats}")
    return total_stats
