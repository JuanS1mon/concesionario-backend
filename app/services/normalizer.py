"""
Normalización de datos de mercado.
Convierte MarketRawListing → MarketListing, matcheando con marcas/modelos internos.
Usa SQL directo para escritura eficiente contra Railway PostgreSQL.
"""
import logging
import statistics
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.pricing import MarketRawListing, MarketListing
from app.models.marca import Marca
from app.models.modelo import Modelo

logger = logging.getLogger(__name__)

MARCA_ALIASES = {
    "vw": "Volkswagen", "volkswagen": "Volkswagen",
    "chevy": "Chevrolet", "chevrolet": "Chevrolet",
    "mercedes benz": "Mercedes-Benz", "mercedes": "Mercedes-Benz", "mb": "Mercedes-Benz",
    "bmw": "BMW", "ford": "Ford", "toyota": "Toyota", "fiat": "Fiat",
    "renault": "Renault", "peugeot": "Peugeot",
    "citroen": "Citroën", "citroën": "Citroën",
    "nissan": "Nissan", "honda": "Honda", "hyundai": "Hyundai", "kia": "Kia",
    "jeep": "Jeep", "audi": "Audi", "dodge": "Dodge", "ram": "RAM",
    "chery": "Chery", "suzuki": "Suzuki", "mitsubishi": "Mitsubishi",
    "subaru": "Subaru", "mazda": "Mazda", "volvo": "Volvo",
    "land rover": "Land Rover", "landrover": "Land Rover",
    "porsche": "Porsche", "ds": "DS",
    "alfa romeo": "Alfa Romeo", "alfaromeo": "Alfa Romeo",
    "mini": "MINI", "lexus": "Lexus", "jaguar": "Jaguar",
}


def _normalizar_nombre(nombre: str) -> str:
    return nombre.strip().lower()


def _es_outlier(precio: float, precios: list[float], desviaciones: float = 2.0) -> bool:
    if len(precios) < 3:
        return False
    try:
        media = statistics.mean(precios)
        desvio = statistics.stdev(precios)
        if desvio == 0:
            return False
        return abs(precio - media) > desviaciones * desvio
    except statistics.StatisticsError:
        return False


def normalizar_listings(db: Session) -> dict:
    """
    Convierte raw listings → market listings usando SQL directo.
    1. Lee todos los raw no procesados en memoria (SELECT)
    2. Matchea marca/modelo en Python (sin queries)
    3. Escribe con SQL directo (INSERT batch + UPDATE batch)
    """
    stats = {"procesados": 0, "normalizados": 0, "sin_match": 0, "outliers_filtrados": 0}

    # ── Leer todo a memoria con SQL directo ──
    raws = db.execute(text(
        "SELECT id, fuente, url, marca_raw, modelo_raw, anio, km, precio, moneda, "
        "ubicacion, fecha_publicacion, fecha_scraping "
        "FROM market_raw_listings WHERE procesado = false"
    )).fetchall()

    if not raws:
        return stats

    # ── Marcas y modelos en memoria ──
    marcas_rows = db.execute(text("SELECT id, nombre FROM marcas")).fetchall()
    modelos_rows = db.execute(text("SELECT id, marca_id, nombre FROM modelos")).fetchall()

    marcas_por_nombre: dict[str, tuple[int, str]] = {}
    for mid, nombre in marcas_rows:
        marcas_por_nombre[nombre.lower()] = (mid, nombre)

    modelos_por_marca: dict[int, dict[str, int]] = {}
    for mid, marca_id, nombre in modelos_rows:
        modelos_por_marca.setdefault(marca_id, {})
        modelos_por_marca[marca_id][nombre.lower()] = mid

    existing_urls = set(
        row[0] for row in db.execute(text(
            "SELECT url FROM market_listings WHERE url IS NOT NULL"
        )).fetchall()
    )

    def buscar_marca(marca_raw: str) -> int | None:
        if not marca_raw:
            return None
        norm = _normalizar_nombre(marca_raw)
        oficial = MARCA_ALIASES.get(norm, marca_raw.strip())
        r = marcas_por_nombre.get(oficial.lower())
        if r:
            return r[0]
        for key, (mid, _) in marcas_por_nombre.items():
            if oficial.lower() in key or key in oficial.lower():
                return mid
        r = marcas_por_nombre.get(marca_raw.strip().lower())
        return r[0] if r else None

    def buscar_modelo(modelo_raw: str, marca_id: int) -> int | None:
        if not modelo_raw:
            return None
        modelos = modelos_por_marca.get(marca_id, {})
        mid = modelos.get(modelo_raw.strip().lower())
        if mid:
            return mid
        ml = modelo_raw.strip().lower()
        for key, mid in modelos.items():
            if ml in key or key in ml:
                return mid
        return None

    # ── Agrupar precios para outliers ──
    precios_grupo: dict[str, list[float]] = {}
    for row in raws:
        precio, marca_raw, anio = row[7], row[3], row[5]
        if precio and marca_raw and anio:
            key = f"{_normalizar_nombre(marca_raw)}_{anio}"
            precios_grupo.setdefault(key, []).append(float(precio))

    # ── Procesar en memoria ──
    ids_procesados = []
    inserts = []

    for row in raws:
        raw_id, fuente, url = row[0], row[1], row[2]
        marca_raw, modelo_raw, anio = row[3], row[4], row[5]
        km, precio, moneda = row[6], row[7], row[8]
        ubicacion, fecha_pub, fecha_scr = row[9], row[10], row[11]

        stats["procesados"] += 1
        ids_procesados.append(raw_id)

        if not precio or not marca_raw:
            stats["sin_match"] += 1
            continue

        marca_id = buscar_marca(marca_raw)
        if not marca_id:
            stats["sin_match"] += 1
            continue

        modelo_id = buscar_modelo(modelo_raw or "", marca_id)
        if not modelo_id:
            stats["sin_match"] += 1
            continue

        key = f"{_normalizar_nombre(marca_raw)}_{anio}"
        precios = precios_grupo.get(key, [])
        if _es_outlier(float(precio), precios):
            stats["outliers_filtrados"] += 1
            continue

        if url and url in existing_urls:
            continue

        inserts.append({
            "raw_listing_id": raw_id, "fuente": fuente,
            "marca_id": marca_id, "modelo_id": modelo_id,
            "anio": anio or 0, "km": km, "precio": float(precio),
            "moneda": moneda or "ARS", "ubicacion": ubicacion,
            "url": url, "activo": True,
            "fecha_publicacion": fecha_pub, "fecha_scraping": fecha_scr,
        })
        if url:
            existing_urls.add(url)
        stats["normalizados"] += 1

    # ── Escribir con SQL en lotes ──
    BATCH = 25

    # 1. UPDATE procesado = true en lotes
    for i in range(0, len(ids_procesados), BATCH):
        batch_ids = ids_procesados[i:i + BATCH]
        placeholders = ",".join(str(x) for x in batch_ids)
        db.execute(text(f"UPDATE market_raw_listings SET procesado = true WHERE id IN ({placeholders})"))
        db.commit()

    # 2. INSERT market_listings en lotes
    if inserts:
        insert_sql = text(
            "INSERT INTO market_listings "
            "(raw_listing_id, fuente, marca_id, modelo_id, anio, km, precio, moneda, "
            "ubicacion, url, activo, fecha_publicacion, fecha_scraping) "
            "VALUES (:raw_listing_id, :fuente, :marca_id, :modelo_id, :anio, :km, :precio, "
            ":moneda, :ubicacion, :url, :activo, :fecha_publicacion, :fecha_scraping)"
        )
        for i in range(0, len(inserts), BATCH):
            batch = inserts[i:i + BATCH]
            for row_data in batch:
                db.execute(insert_sql, row_data)
            db.commit()

    logger.info(f"Normalización completada: {stats}")
    return stats
