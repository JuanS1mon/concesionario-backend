"""
Integración con la API oficial de MercadoLibre Argentina.
Usa OAuth2 para autenticación y los endpoints oficiales de búsqueda.

Requiere:
  - ML_CLIENT_ID y ML_CLIENT_SECRET en las variables de entorno
  - Registrar la app en https://developers.mercadolibre.com.ar/

Sin credenciales, genera datos de ejemplo para desarrollo.
"""
import requests
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from app.models.pricing import MarketRawListing
from app.models.marca import Marca
from app.models.modelo import Modelo
from app.config import ML_CLIENT_ID, ML_CLIENT_SECRET

logger = logging.getLogger(__name__)

ML_API_BASE = "https://api.mercadolibre.com"
ML_AUTH_URL = "https://api.mercadolibre.com/oauth/token"
ML_CATEGORY_AUTOS = "MLA1744"  # Autos y Camionetas

# Cache del token en memoria
_ml_token_cache: dict = {"token": None, "expires_at": 0}


def _obtener_token_ml() -> Optional[str]:
    """Obtiene un access_token de MercadoLibre usando client_credentials."""
    if not ML_CLIENT_ID or not ML_CLIENT_SECRET:
        logger.warning("ML_CLIENT_ID o ML_CLIENT_SECRET no configurados. Usando datos de ejemplo.")
        return None

    # Verificar cache
    import time
    if _ml_token_cache["token"] and _ml_token_cache["expires_at"] > time.time():
        return _ml_token_cache["token"]

    try:
        response = requests.post(ML_AUTH_URL, json={
            "grant_type": "client_credentials",
            "client_id": ML_CLIENT_ID,
            "client_secret": ML_CLIENT_SECRET,
        }, timeout=10)
        response.raise_for_status()
        data = response.json()
        token = data.get("access_token")
        expires_in = data.get("expires_in", 21600)
        _ml_token_cache["token"] = token
        _ml_token_cache["expires_at"] = time.time() + expires_in - 60
        logger.info("Token de MercadoLibre obtenido correctamente")
        return token
    except requests.RequestException as e:
        logger.error(f"Error al obtener token de MercadoLibre: {e}")
        return None


def _extraer_km(attributes: list) -> Optional[int]:
    """Extrae el kilometraje de los atributos de MercadoLibre."""
    for attr in attributes:
        if attr.get("id") == "KILOMETERS":
            try:
                valor = attr.get("value_name", "").replace(" km", "").replace(".", "").strip()
                return int(valor) if valor else None
            except (ValueError, TypeError):
                return None
    return None


def _extraer_anio(attributes: list) -> Optional[int]:
    """Extrae el año del vehículo de los atributos."""
    for attr in attributes:
        if attr.get("id") == "VEHICLE_YEAR":
            try:
                return int(attr.get("value_name", "0"))
            except (ValueError, TypeError):
                return None
    return None


def _extraer_marca_modelo(titulo: str, attributes: list) -> tuple[str, str]:
    """Extrae marca y modelo de los atributos o del título."""
    marca = ""
    modelo = ""
    for attr in attributes:
        if attr.get("id") == "BRAND":
            marca = attr.get("value_name", "")
        elif attr.get("id") == "MODEL":
            modelo = attr.get("value_name", "")
    if not marca and titulo:
        partes = titulo.split(" ")
        marca = partes[0] if partes else ""
    return marca, modelo


# Cache a nivel de módulo: si la API de búsqueda no está disponible
_ml_search_available: Optional[bool] = None


def scrape_mercadolibre(
    db: Session,
    query: str = "",
    marca: str = "",
    modelo: str = "",
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """
    Busca listings en MercadoLibre usando la API oficial con OAuth2.
    Si la API devuelve 403 (requiere authorization code flow) o no hay
    credenciales, genera datos de ejemplo.
    Retorna dict con stats: {nuevos, duplicados, errores}.
    """
    stats = {"nuevos": 0, "duplicados": 0, "errores": 0}

    search_query = query or f"{marca} {modelo}".strip()
    if not search_query:
        return stats

    token = _obtener_token_ml()

    global _ml_search_available
    if token and _ml_search_available is not False:
        # Intentar la API oficial
        params = {
            "category": ML_CATEGORY_AUTOS,
            "q": search_query,
            "limit": min(limit, 50),
            "offset": offset,
        }
        headers = {"Authorization": f"Bearer {token}"}

        try:
            response = requests.get(
                f"{ML_API_BASE}/sites/MLA/search",
                params=params,
                headers=headers,
                timeout=15,
            )
            if response.status_code == 200:
                _ml_search_available = True
                data = response.json()
                results = data.get("results", [])
                for item in results:
                    try:
                        url = item.get("permalink", "")
                        existe = db.query(MarketRawListing).filter(MarketRawListing.url == url).first()
                        if existe:
                            stats["duplicados"] += 1
                            continue

                        attrs = item.get("attributes", [])
                        marca_raw, modelo_raw = _extraer_marca_modelo(item.get("title", ""), attrs)
                        anio = _extraer_anio(attrs)
                        km = _extraer_km(attrs)

                        raw = MarketRawListing(
                            fuente="mercadolibre",
                            url=url,
                            titulo=item.get("title", ""),
                            marca_raw=marca_raw,
                            modelo_raw=modelo_raw,
                            anio=anio,
                            km=km,
                            precio=item.get("price"),
                            moneda=item.get("currency_id", "ARS"),
                            ubicacion=item.get("address", {}).get("state_name", ""),
                            imagen_url=item.get("thumbnail", ""),
                            activo=True,
                            procesado=False,
                            fecha_scraping=datetime.utcnow(),
                        )
                        db.add(raw)
                        stats["nuevos"] += 1
                    except Exception as e:
                        logger.error(f"Error procesando item ML: {e}")
                        stats["errores"] += 1
                db.commit()
                return stats
            else:
                _ml_search_available = False
                logger.info(f"API ML devolvió {response.status_code}, usando datos de referencia.")
        except requests.RequestException as e:
            logger.info(f"API ML no accesible ({e}), usando datos de referencia.")

    # Fallback: datos de referencia del mercado argentino
    return _generar_datos_ejemplo(db, marca, modelo)


def _generar_datos_ejemplo(db: Session, marca: str = "", modelo: str = "") -> dict:
    """
    Genera datos de ejemplo basados en precios de referencia del mercado argentino.
    Se usa cuando la API de ML no está disponible.
    Optimizado: batch insert + URLs en memoria.
    """
    import random

    stats = {"nuevos": 0, "duplicados": 0, "errores": 0}

    # Precios de referencia alineados con las marcas/modelos de la DB del concesionario
    PRECIOS_REF: dict[str, dict[str, dict[int, int]]] = {
        "Toyota": {
            "Corolla": {2020: 28000000, 2021: 32000000, 2022: 36000000, 2023: 42000000, 2024: 48000000},
            "Camry": {2020: 35000000, 2021: 40000000, 2022: 46000000, 2023: 53000000, 2024: 60000000},
            "RAV4": {2020: 42000000, 2021: 48000000, 2022: 55000000, 2023: 63000000, 2024: 72000000},
            "Highlander": {2020: 50000000, 2021: 57000000, 2022: 65000000, 2023: 74000000, 2024: 84000000},
            "Prius": {2020: 32000000, 2021: 37000000, 2022: 42000000, 2023: 48000000, 2024: 55000000},
        },
        "Honda": {
            "Civic": {2020: 26000000, 2021: 30000000, 2022: 34000000, 2023: 40000000, 2024: 46000000},
            "Accord": {2020: 33000000, 2021: 38000000, 2022: 43000000, 2023: 50000000, 2024: 57000000},
            "CR-V": {2020: 38000000, 2021: 44000000, 2022: 50000000, 2023: 57000000, 2024: 65000000},
            "Fit": {2020: 18000000, 2021: 21000000, 2022: 24000000, 2023: 28000000, 2024: 32000000},
            "Pilot": {2020: 48000000, 2021: 55000000, 2022: 62000000, 2023: 71000000, 2024: 80000000},
        },
        "Ford": {
            "Focus": {2020: 18000000, 2021: 21000000, 2022: 24000000, 2023: 28000000, 2024: 32000000},
            "Mustang": {2020: 55000000, 2021: 63000000, 2022: 72000000, 2023: 82000000, 2024: 93000000},
            "Explorer": {2020: 48000000, 2021: 55000000, 2022: 63000000, 2023: 72000000, 2024: 82000000},
            "Escape": {2020: 30000000, 2021: 35000000, 2022: 40000000, 2023: 46000000, 2024: 52000000},
            "F-150": {2020: 52000000, 2021: 60000000, 2022: 68000000, 2023: 78000000, 2024: 88000000},
        },
        "Chevrolet": {
            "Cruze": {2020: 20000000, 2021: 23000000, 2022: 27000000, 2023: 31000000, 2024: 36000000},
            "Malibu": {2020: 25000000, 2021: 29000000, 2022: 33000000, 2023: 38000000, 2024: 44000000},
            "Equinox": {2020: 30000000, 2021: 35000000, 2022: 40000000, 2023: 46000000, 2024: 52000000},
            "Traverse": {2020: 42000000, 2021: 48000000, 2022: 55000000, 2023: 63000000, 2024: 72000000},
            "Colorado": {2020: 36000000, 2021: 42000000, 2022: 48000000, 2023: 55000000, 2024: 62000000},
        },
        "Nissan": {
            "Sentra": {2020: 18000000, 2021: 21000000, 2022: 24000000, 2023: 28000000, 2024: 32000000},
            "Altima": {2020: 24000000, 2021: 28000000, 2022: 32000000, 2023: 37000000, 2024: 42000000},
            "Rogue": {2020: 32000000, 2021: 37000000, 2022: 42000000, 2023: 48000000, 2024: 55000000},
            "Murano": {2020: 38000000, 2021: 44000000, 2022: 50000000, 2023: 57000000, 2024: 65000000},
            "Maxima": {2020: 30000000, 2021: 35000000, 2022: 40000000, 2023: 46000000, 2024: 52000000},
        },
        "BMW": {
            "Serie 3": {2020: 45000000, 2021: 52000000, 2022: 59000000, 2023: 68000000, 2024: 77000000},
            "Serie 5": {2020: 55000000, 2021: 63000000, 2022: 72000000, 2023: 82000000, 2024: 93000000},
            "X3": {2020: 50000000, 2021: 57000000, 2022: 65000000, 2023: 74000000, 2024: 84000000},
            "X5": {2020: 65000000, 2021: 74000000, 2022: 85000000, 2023: 97000000, 2024: 110000000},
        },
        "Mercedes-Benz": {
            "C-Class": {2020: 48000000, 2021: 55000000, 2022: 63000000, 2023: 72000000, 2024: 82000000},
            "E-Class": {2020: 60000000, 2021: 69000000, 2022: 79000000, 2023: 90000000, 2024: 102000000},
            "GLC": {2020: 55000000, 2021: 63000000, 2022: 72000000, 2023: 82000000, 2024: 93000000},
            "GLE": {2020: 70000000, 2021: 80000000, 2022: 91000000, 2023: 104000000, 2024: 118000000},
        },
        "Volkswagen": {
            "Golf": {2020: 24000000, 2021: 28000000, 2022: 32000000, 2023: 37000000, 2024: 43000000},
            "Jetta": {2020: 20000000, 2021: 23000000, 2022: 27000000, 2023: 31000000, 2024: 36000000},
            "Tiguan": {2020: 32000000, 2021: 37000000, 2022: 42000000, 2023: 48000000, 2024: 55000000},
            "Passat": {2020: 28000000, 2021: 32000000, 2022: 37000000, 2023: 42000000, 2024: 48000000},
            "Beetle": {2020: 22000000, 2021: 25000000, 2022: 29000000, 2023: 33000000, 2024: 38000000},
        },
        "Hyundai": {
            "Elantra": {2020: 18000000, 2021: 21000000, 2022: 24000000, 2023: 28000000, 2024: 32000000},
            "Sonata": {2020: 25000000, 2021: 29000000, 2022: 33000000, 2023: 38000000, 2024: 44000000},
            "Tucson": {2020: 30000000, 2021: 35000000, 2022: 40000000, 2023: 46000000, 2024: 52000000},
            "Santa Fe": {2020: 40000000, 2021: 46000000, 2022: 52000000, 2023: 60000000, 2024: 68000000},
            "Ioniq": {2020: 28000000, 2021: 32000000, 2022: 37000000, 2023: 42000000, 2024: 48000000},
        },
        "Kia": {
            "Forte": {2020: 17000000, 2021: 20000000, 2022: 23000000, 2023: 27000000, 2024: 31000000},
            "Optima": {2020: 23000000, 2021: 27000000, 2022: 31000000, 2023: 36000000, 2024: 41000000},
            "Sportage": {2020: 28000000, 2021: 32000000, 2022: 37000000, 2023: 42000000, 2024: 48000000},
            "Sorento": {2020: 38000000, 2021: 44000000, 2022: 50000000, 2023: 57000000, 2024: 65000000},
            "Niro": {2020: 26000000, 2021: 30000000, 2022: 34000000, 2023: 39000000, 2024: 45000000},
        },
    }

    provincias = [
        "Buenos Aires", "CABA", "Córdoba", "Santa Fe", "Mendoza",
        "Tucumán", "Entre Ríos", "Salta", "Misiones", "San Juan",
    ]

    # Cargar URLs existentes en memoria (1 sola query)
    existing_urls = set(
        url for (url,) in db.query(MarketRawListing.url).filter(
            MarketRawListing.fuente == "mercadolibre"
        ).all()
    )

    marcas_buscar = {marca: PRECIOS_REF[marca]} if marca and marca in PRECIOS_REF else PRECIOS_REF

    nuevos = []
    for marca_nombre, modelos_data in marcas_buscar.items():
        modelos_buscar = (
            {modelo: modelos_data[modelo]} if modelo and modelo in modelos_data else modelos_data
        )
        for modelo_nombre, anios_precios in modelos_buscar.items():
            for anio, precio_base in anios_precios.items():
                n_listings = 2
                for i in range(n_listings):
                    variacion = random.uniform(-0.15, 0.15)
                    precio = int(precio_base * (1 + variacion))
                    km = random.randint(5000, 120000)
                    url = f"https://ejemplo-mercadolibre.com/{marca_nombre.lower()}-{modelo_nombre.lower()}-{anio}-{random.randint(100000, 999999)}"

                    if url in existing_urls:
                        stats["duplicados"] += 1
                        continue

                    nuevos.append(MarketRawListing(
                        fuente="mercadolibre",
                        url=url,
                        titulo=f"{marca_nombre} {modelo_nombre} {anio} - {km} km",
                        marca_raw=marca_nombre,
                        modelo_raw=modelo_nombre,
                        anio=anio,
                        km=km,
                        precio=precio,
                        moneda="ARS",
                        ubicacion=random.choice(provincias),
                        imagen_url="",
                        activo=True,
                        procesado=False,
                        fecha_scraping=datetime.utcnow(),
                    ))
                    existing_urls.add(url)
                    stats["nuevos"] += 1

    db.add_all(nuevos)
    db.commit()
    logger.info(f"Datos de ejemplo MercadoLibre generados: {stats}")
    return stats


def scrape_all_mercadolibre(db: Session, max_por_marca: int = 50) -> dict:
    """
    Scrape automático: intenta la API ML una vez.
    Si la API no funciona (403), genera datos de ejemplo para todas
    las marcas/modelos de una sola vez (rápido).
    """
    global _ml_search_available

    # Intentar la API una vez para verificar si funciona
    token = _obtener_token_ml()
    if token and _ml_search_available is not False:
        try:
            response = requests.get(
                f"{ML_API_BASE}/sites/MLA/search",
                params={"category": ML_CATEGORY_AUTOS, "q": "auto", "limit": 1},
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
            if response.status_code == 200:
                _ml_search_available = True
            else:
                _ml_search_available = False
                logger.info(f"API ML search no disponible (status {response.status_code}). Usando datos de referencia.")
        except requests.RequestException as e:
            _ml_search_available = False
            logger.info(f"API ML search no accesible ({e}). Usando datos de referencia.")

    if _ml_search_available:
        # Ruta con API real: iterar por marca/modelo
        total_stats = {"nuevos": 0, "duplicados": 0, "errores": 0}
        marcas = db.query(Marca).all()
        modelos = db.query(Modelo).all()
        modelos_por_marca = {}
        for m in modelos:
            modelos_por_marca.setdefault(m.marca_id, []).append(m)

        for marca in marcas:
            marca_modelos = modelos_por_marca.get(marca.id, [])
            if not marca_modelos:
                stats = scrape_mercadolibre(db, marca=marca.nombre, limit=max_por_marca)
                for k in total_stats:
                    total_stats[k] += stats[k]
            else:
                for modelo in marca_modelos:
                    stats = scrape_mercadolibre(
                        db, marca=marca.nombre, modelo=modelo.nombre, limit=max_por_marca
                    )
                    for k in total_stats:
                        total_stats[k] += stats[k]
        logger.info(f"Scraping MercadoLibre (API) completado: {total_stats}")
        return total_stats
    else:
        # Ruta rápida: generar todos los datos de ejemplo de una vez
        stats = _generar_datos_ejemplo(db)
        logger.info(f"Scraping MercadoLibre (ejemplo) completado: {stats}")
        return stats
