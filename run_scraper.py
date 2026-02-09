#!/usr/bin/env python
"""
Script standalone para ejecutar el scraping de datos de mercado.
Puede ejecutarse vía cron o manualmente.

Uso:
    python run_scraper.py                  # Scraping + normalización
    python run_scraper.py --fuente kavak   # Solo Kavak
    python run_scraper.py --no-normalize   # Sin normalizar
"""
import argparse
import logging
import sys
import os

# Asegurar que el directorio raíz del backend esté en el path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.services.scraper_mercadolibre import scrape_all_mercadolibre
from app.services.scraper_kavak import scrape_all_kavak
from app.services.normalizer import normalizar_listings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("run_scraper")


def main():
    parser = argparse.ArgumentParser(description="Scraper de datos de mercado")
    parser.add_argument(
        "--fuente",
        choices=["mercadolibre", "kavak", "all"],
        default="all",
        help="Fuente a scrapear (default: all)",
    )
    parser.add_argument(
        "--no-normalize",
        action="store_true",
        help="No ejecutar normalización después del scraping",
    )
    parser.add_argument(
        "--max-por-marca",
        type=int,
        default=50,
        help="Máximo de listings por marca (default: 50)",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        total = {"nuevos": 0, "duplicados": 0, "errores": 0}

        if args.fuente in ("mercadolibre", "all"):
            logger.info("Iniciando scraping de MercadoLibre...")
            stats = scrape_all_mercadolibre(db, max_por_marca=args.max_por_marca)
            logger.info(f"MercadoLibre: {stats}")
            for k in total:
                total[k] += stats[k]

        if args.fuente in ("kavak", "all"):
            logger.info("Iniciando scraping de Kavak...")
            stats = scrape_all_kavak(db, max_por_marca=args.max_por_marca)
            logger.info(f"Kavak: {stats}")
            for k in total:
                total[k] += stats[k]

        logger.info(f"Scraping total: {total}")

        if not args.no_normalize:
            logger.info("Iniciando normalización...")
            norm_stats = normalizar_listings(db)
            logger.info(f"Normalización: {norm_stats}")

        logger.info("Proceso completado exitosamente.")
    except Exception as e:
        logger.error(f"Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
