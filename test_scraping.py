"""Test directo de scraping (sin API, directo a funciones)."""
import sys
import os
import time
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from app.database import SessionLocal
from app.services.scraper_mercadolibre import scrape_all_mercadolibre
from app.services.scraper_kavak import scrape_all_kavak
from app.services.normalizer import normalizar_listings
from app.models.pricing import MarketRawListing, MarketListing

# Limpiar datos anteriores (sesión separada)
print("=== LIMPIEZA ===")
db = SessionLocal()
db.query(MarketListing).delete()
db.query(MarketRawListing).delete()
db.commit()
db.close()
print("  Datos anteriores eliminados")

# 1. Scrape all ML (sesión nueva)
print("\n=== SCRAPE ALL MERCADOLIBRE ===")
db = SessionLocal()
t0 = time.time()
stats_ml = scrape_all_mercadolibre(db)
t1 = time.time()
raw_count_ml = db.query(MarketRawListing).filter(MarketRawListing.fuente == "mercadolibre").count()
db.close()
print(f"  Stats ML: {stats_ml}")
print(f"  Tiempo: {t1-t0:.1f}s")
print(f"  Raw listings ML en DB: {raw_count_ml}")

# 2. Scrape all Kavak (sesión nueva)
print("\n=== SCRAPE ALL KAVAK ===")
db = SessionLocal()
t0 = time.time()
stats_kv = scrape_all_kavak(db)
t1 = time.time()
raw_count_kv = db.query(MarketRawListing).filter(MarketRawListing.fuente == "kavak").count()
total_raw = db.query(MarketRawListing).count()
db.close()
print(f"  Stats Kavak: {stats_kv}")
print(f"  Tiempo: {t1-t0:.1f}s")
print(f"  Raw listings Kavak en DB: {raw_count_kv}")
print(f"  Total raw listings: {total_raw}")

# 3. Normalizar (sesión nueva)
print("\n=== NORMALIZACIÓN ===")
db = SessionLocal()
t0 = time.time()
stats_norm = normalizar_listings(db)
t1 = time.time()
market_count = db.query(MarketListing).count()
db.close()
print(f"  Stats normalización: {stats_norm}")
print(f"  Tiempo: {t1-t0:.1f}s")
print(f"  Market listings normalizados: {market_count}")

print("\n=== TEST COMPLETADO ===")

