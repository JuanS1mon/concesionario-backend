"""CLI minimal para tareas diarias: scraping, normalización y análisis.
Uso: `python -m app.cli daily-update` o `python -m app.cli`.
"""
from app.database import SessionLocal
from app.services.scraper_mercadolibre import scrape_all_mercadolibre
from app.services.scraper_kavak import scrape_all_kavak
from app.services.scraper_deruedas import scrape_all_deruedas
from app.services.scraper_preciosdeautos import scrape_all_preciosdeautos
from app.services.scraper_ai import scrape_all_ai
from app.services.normalizer import normalizar_listings
from app.services.pricing_engine import analizar_inventario

def daily_update():
    db = SessionLocal()
    try:
        total = {"nuevos": 0, "duplicados": 0, "errores": 0}

        for fn in (scrape_all_mercadolibre, scrape_all_kavak, scrape_all_deruedas, scrape_all_preciosdeautos):
            try:
                stats = fn(db)
                for k in total:
                    total[k] += stats.get(k, 0)
            except Exception as e:
                print(f"Error en scraper {fn.__name__}: {e}")

        # AI scraper (si está configurado puede fallar si no hay API key)
        try:
            stats_ai = scrape_all_ai(db)
            for k in total:
                total[k] += stats_ai.get(k, 0)
        except Exception as e:
            print(f"AI scraper skipped/error: {e}")

        print("Scraping finalizado:", total)

        # Normalización
        try:
            norm_stats = normalizar_listings(db)
            print("Normalización:", norm_stats)
        except Exception as e:
            print(f"Normalización falló: {e}")

        # Analizar inventario
        try:
            resultados = analizar_inventario(db)
            print(f"Análisis completado para {len(resultados)} autos")
        except Exception as e:
            print(f"Análisis de inventario falló: {e}")

    finally:
        db.close()


if __name__ == "__main__":
    daily_update()
