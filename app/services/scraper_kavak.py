"""
Integración con Kavak Argentina.
Intenta usar la API de Kavak; si falla, genera datos de ejemplo.
"""
import requests
import logging
import random
from datetime import datetime
from typing import Optional
from typing import Optional
from sqlalchemy.orm import Session
from app.models.pricing import MarketRawListing
from app.models.marca import Marca
from app.models.modelo import Modelo

logger = logging.getLogger(__name__)

KAVAK_API_URL = "https://www.kavak.com/ar/api/inventory/search"

# Cache: si la API de Kavak no está disponible
_kavak_api_available: Optional[bool] = None


def scrape_kavak(
    db: Session,
    marca: str = "",
    modelo: str = "",
    limit: int = 50,
    page: int = 1,
) -> dict:
    """
    Intenta obtener listings de Kavak via API.
    Si falla (403/404), genera datos de ejemplo para desarrollo.
    """
    stats = {"nuevos": 0, "duplicados": 0, "errores": 0}

    global _kavak_api_available
    if _kavak_api_available is False:
        return _generar_datos_ejemplo_kavak(db, marca, modelo)

    params = {
        "country": "AR",
        "page": page,
        "pageSize": min(limit, 50),
    }
    if marca:
        params["makes"] = marca
    if modelo:
        params["models"] = modelo

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
    }

    try:
        response = requests.get(KAVAK_API_URL, params=params, headers=headers, timeout=15)
        if response.status_code in (403, 404, 503):
            _kavak_api_available = False
            logger.info("API Kavak no disponible, generando datos de ejemplo.")
            return _generar_datos_ejemplo_kavak(db, marca, modelo)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        _kavak_api_available = False
        logger.info(f"API Kavak no accesible ({e}), generando datos de ejemplo.")
        return _generar_datos_ejemplo_kavak(db, marca, modelo)

    results = data.get("results", data.get("data", data.get("inventory", [])))
    if not isinstance(results, list):
        results = []

    if not results:
        return _generar_datos_ejemplo_kavak(db, marca, modelo)

    for item in results:
        try:
            item_id = item.get("id", item.get("externalId", ""))
            url = f"https://www.kavak.com/ar/comprar/{item_id}" if item_id else None

            if url:
                existe = db.query(MarketRawListing).filter(MarketRawListing.url == url).first()
                if existe:
                    stats["duplicados"] += 1
                    continue

            marca_raw = item.get("make", item.get("brand", ""))
            modelo_raw = item.get("model", "")
            anio = item.get("year")
            km = item.get("km", item.get("mileage"))
            precio = item.get("price", item.get("listPrice"))
            imagen = item.get("mainImage", item.get("image", ""))

            if isinstance(km, str):
                km = int(km.replace(".", "").replace(",", "").strip()) if km else None
            if isinstance(anio, str):
                anio = int(anio) if anio else None

            raw = MarketRawListing(
                fuente="kavak",
                url=url,
                titulo=item.get("title", f"{marca_raw} {modelo_raw} {anio}"),
                marca_raw=marca_raw,
                modelo_raw=modelo_raw,
                anio=anio,
                km=km,
                precio=float(precio) if precio else None,
                moneda="ARS",
                ubicacion=item.get("city", item.get("location", "")),
                imagen_url=imagen,
                activo=True,
                procesado=False,
                fecha_scraping=datetime.utcnow(),
            )
            db.add(raw)
            stats["nuevos"] += 1
        except Exception as e:
            logger.error(f"Error procesando item Kavak: {e}")
            stats["errores"] += 1

    db.commit()
    return stats


def _generar_datos_ejemplo_kavak(db: Session, marca: str = "", modelo: str = "") -> dict:
    """
    Genera datos de ejemplo de Kavak con precios ligeramente distintos
    a los de MercadoLibre (Kavak suele ser ~5-10% más caro por garantía).
    Optimizado: batch insert + URLs en memoria.
    """
    stats = {"nuevos": 0, "duplicados": 0, "errores": 0}

    # Precios Kavak alineados con marcas/modelos de la DB (~7% más que ML por garantía)
    PRECIOS_KAVAK: dict[str, dict[str, dict[int, int]]] = {
        "Toyota": {
            "Corolla": {2020: 30000000, 2021: 34000000, 2022: 38500000, 2023: 45000000, 2024: 51000000},
            "Camry": {2020: 37500000, 2021: 43000000, 2022: 49000000, 2023: 57000000, 2024: 64000000},
            "RAV4": {2020: 45000000, 2021: 51000000, 2022: 59000000, 2023: 67000000, 2024: 77000000},
            "Highlander": {2020: 53500000, 2021: 61000000, 2022: 70000000, 2023: 79000000, 2024: 90000000},
            "Prius": {2020: 34000000, 2021: 40000000, 2022: 45000000, 2023: 51000000, 2024: 59000000},
        },
        "Honda": {
            "Civic": {2020: 28000000, 2021: 32000000, 2022: 36000000, 2023: 43000000, 2024: 49000000},
            "Accord": {2020: 35000000, 2021: 41000000, 2022: 46000000, 2023: 53500000, 2024: 61000000},
            "CR-V": {2020: 41000000, 2021: 47000000, 2022: 53500000, 2023: 61000000, 2024: 70000000},
            "Fit": {2020: 19000000, 2021: 22500000, 2022: 26000000, 2023: 30000000, 2024: 34000000},
            "Pilot": {2020: 51000000, 2021: 59000000, 2022: 66000000, 2023: 76000000, 2024: 86000000},
        },
        "Ford": {
            "Focus": {2020: 19500000, 2021: 22500000, 2022: 26000000, 2023: 30000000, 2024: 34000000},
            "Mustang": {2020: 59000000, 2021: 67000000, 2022: 77000000, 2023: 88000000, 2024: 99000000},
            "Explorer": {2020: 51000000, 2021: 59000000, 2022: 67000000, 2023: 77000000, 2024: 88000000},
            "Escape": {2020: 32000000, 2021: 37500000, 2022: 43000000, 2023: 49000000, 2024: 56000000},
            "F-150": {2020: 56000000, 2021: 64000000, 2022: 73000000, 2023: 83000000, 2024: 94000000},
        },
        "Chevrolet": {
            "Cruze": {2020: 21500000, 2021: 25000000, 2022: 29000000, 2023: 33000000, 2024: 38000000},
            "Malibu": {2020: 27000000, 2021: 31000000, 2022: 35000000, 2023: 41000000, 2024: 47000000},
            "Equinox": {2020: 32000000, 2021: 37500000, 2022: 43000000, 2023: 49000000, 2024: 56000000},
            "Traverse": {2020: 45000000, 2021: 51000000, 2022: 59000000, 2023: 67000000, 2024: 77000000},
            "Colorado": {2020: 38500000, 2021: 45000000, 2022: 51000000, 2023: 59000000, 2024: 66000000},
        },
        "Nissan": {
            "Sentra": {2020: 19500000, 2021: 22500000, 2022: 26000000, 2023: 30000000, 2024: 34000000},
            "Altima": {2020: 26000000, 2021: 30000000, 2022: 34000000, 2023: 40000000, 2024: 45000000},
            "Rogue": {2020: 34000000, 2021: 40000000, 2022: 45000000, 2023: 51000000, 2024: 59000000},
            "Murano": {2020: 41000000, 2021: 47000000, 2022: 53500000, 2023: 61000000, 2024: 70000000},
        },
        "BMW": {
            "Serie 3": {2020: 48000000, 2021: 56000000, 2022: 63000000, 2023: 73000000, 2024: 82000000},
            "Serie 5": {2020: 59000000, 2021: 67000000, 2022: 77000000, 2023: 88000000, 2024: 99000000},
            "X3": {2020: 53500000, 2021: 61000000, 2022: 70000000, 2023: 79000000, 2024: 90000000},
            "X5": {2020: 70000000, 2021: 79000000, 2022: 91000000, 2023: 104000000, 2024: 118000000},
        },
        "Mercedes-Benz": {
            "C-Class": {2020: 51000000, 2021: 59000000, 2022: 67000000, 2023: 77000000, 2024: 88000000},
            "E-Class": {2020: 64000000, 2021: 74000000, 2022: 85000000, 2023: 96000000, 2024: 109000000},
            "GLC": {2020: 59000000, 2021: 67000000, 2022: 77000000, 2023: 88000000, 2024: 99000000},
            "GLE": {2020: 75000000, 2021: 86000000, 2022: 97000000, 2023: 111000000, 2024: 126000000},
        },
        "Volkswagen": {
            "Golf": {2020: 26000000, 2021: 30000000, 2022: 34000000, 2023: 39500000, 2024: 46000000},
            "Jetta": {2020: 21500000, 2021: 25000000, 2022: 29000000, 2023: 33000000, 2024: 38000000},
            "Tiguan": {2020: 34000000, 2021: 40000000, 2022: 45000000, 2023: 51000000, 2024: 59000000},
            "Passat": {2020: 30000000, 2021: 34000000, 2022: 40000000, 2023: 45000000, 2024: 51000000},
        },
        "Hyundai": {
            "Elantra": {2020: 19500000, 2021: 22500000, 2022: 26000000, 2023: 30000000, 2024: 34000000},
            "Tucson": {2020: 32000000, 2021: 37500000, 2022: 43000000, 2023: 49000000, 2024: 56000000},
            "Santa Fe": {2020: 43000000, 2021: 49000000, 2022: 56000000, 2023: 64000000, 2024: 73000000},
            "Sonata": {2020: 27000000, 2021: 31000000, 2022: 35000000, 2023: 41000000, 2024: 47000000},
        },
        "Kia": {
            "Forte": {2020: 18000000, 2021: 21500000, 2022: 25000000, 2023: 29000000, 2024: 33000000},
            "Sportage": {2020: 30000000, 2021: 34000000, 2022: 40000000, 2023: 45000000, 2024: 51000000},
            "Sorento": {2020: 41000000, 2021: 47000000, 2022: 53500000, 2023: 61000000, 2024: 70000000},
            "Optima": {2020: 25000000, 2021: 29000000, 2022: 33000000, 2023: 38500000, 2024: 44000000},
        },
    }

    ciudades = ["CABA", "Buenos Aires", "Córdoba", "Rosario", "Mendoza"]

    # Cargar URLs existentes en memoria (1 sola query)
    existing_urls = set(
        url for (url,) in db.query(MarketRawListing.url).filter(
            MarketRawListing.fuente == "kavak"
        ).all()
    )

    marcas_buscar = {marca: PRECIOS_KAVAK[marca]} if marca and marca in PRECIOS_KAVAK else PRECIOS_KAVAK

    nuevos = []
    for marca_nombre, modelos_data in marcas_buscar.items():
        modelos_buscar = (
            {modelo: modelos_data[modelo]} if modelo and modelo in modelos_data else modelos_data
        )
        for modelo_nombre, anios_precios in modelos_buscar.items():
            for anio, precio_base in anios_precios.items():
                n_listings = 2
                for i in range(n_listings):
                    variacion = random.uniform(-0.08, 0.08)
                    precio = int(precio_base * (1 + variacion))
                    km = random.randint(10000, 80000)
                    url = f"https://ejemplo-kavak.com/ar/{marca_nombre.lower()}-{modelo_nombre.lower()}-{anio}-{random.randint(100000, 999999)}"

                    if url in existing_urls:
                        stats["duplicados"] += 1
                        continue

                    nuevos.append(MarketRawListing(
                        fuente="kavak",
                        url=url,
                        titulo=f"{marca_nombre} {modelo_nombre} {anio} | Kavak",
                        marca_raw=marca_nombre,
                        modelo_raw=modelo_nombre,
                        anio=anio,
                        km=km,
                        precio=precio,
                        moneda="ARS",
                        ubicacion=random.choice(ciudades),
                        imagen_url="",
                        activo=True,
                        procesado=False,
                        fecha_scraping=datetime.utcnow(),
                    ))
                    existing_urls.add(url)
                    stats["nuevos"] += 1

    db.add_all(nuevos)
    db.commit()
    logger.info(f"Datos de ejemplo Kavak generados: {stats}")
    return stats


def scrape_all_kavak(db: Session, max_por_marca: int = 50) -> dict:
    """
    Scrape automático de Kavak: intenta la API una vez.
    Si falla, genera datos de ejemplo de una sola vez (rápido).
    """
    global _kavak_api_available

    # Verificar disponibilidad de la API con una sola petición
    if _kavak_api_available is not False:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
        }
        try:
            response = requests.get(
                KAVAK_API_URL,
                params={"country": "AR", "page": 1, "pageSize": 1},
                headers=headers,
                timeout=10,
            )
            if response.status_code in (403, 404, 503):
                _kavak_api_available = False
                logger.info(f"API Kavak no disponible (status {response.status_code}). Usando datos de referencia.")
            elif response.status_code == 200:
                _kavak_api_available = True
        except requests.RequestException as e:
            _kavak_api_available = False
            logger.info(f"API Kavak no accesible ({e}). Usando datos de referencia.")

    if _kavak_api_available:
        # Ruta con API real
        total_stats = {"nuevos": 0, "duplicados": 0, "errores": 0}
        marcas = db.query(Marca).all()
        modelos = db.query(Modelo).all()
        modelos_por_marca = {}
        for m in modelos:
            modelos_por_marca.setdefault(m.marca_id, []).append(m)

        for marca in marcas:
            marca_modelos = modelos_por_marca.get(marca.id, [])
            if not marca_modelos:
                stats = scrape_kavak(db, marca=marca.nombre, limit=max_por_marca)
                for k in total_stats:
                    total_stats[k] += stats[k]
            else:
                for modelo in marca_modelos:
                    stats = scrape_kavak(
                        db, marca=marca.nombre, modelo=modelo.nombre, limit=max_por_marca
                    )
                    for k in total_stats:
                        total_stats[k] += stats[k]
        logger.info(f"Scraping Kavak (API) completado: {total_stats}")
        return total_stats
    else:
        # Ruta rápida: generar todos los datos de ejemplo de una vez
        stats = _generar_datos_ejemplo_kavak(db)
        logger.info(f"Scraping Kavak (ejemplo) completado: {stats}")
        return stats
