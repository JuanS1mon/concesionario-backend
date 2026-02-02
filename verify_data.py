"""
Script para verificar los datos actuales en la base de datos
"""
from app.database import SessionLocal
from app.models.marca import Marca
from app.models.modelo import Modelo
from app.models.auto import Auto

def verify_data():
    """Verifica los datos en la base de datos"""
    db = SessionLocal()
    
    try:
        marcas_count = db.query(Marca).count()
        modelos_count = db.query(Modelo).count()
        autos_count = db.query(Auto).count()
        
        print(f"Marcas: {marcas_count}")
        print(f"Modelos: {modelos_count}")
        print(f"Autos: {autos_count}")
        
        if marcas_count > 0:
            print("\nMarcas cargadas:")
            for marca in db.query(Marca).all():
                print(f"  - {marca.nombre}")
        
        if autos_count > 0:
            print(f"\nPrimeros autos cargados:")
            for auto in db.query(Auto).limit(5).all():
                marca = db.query(Marca).filter(Marca.id == auto.marca_id).first()
                modelo = db.query(Modelo).filter(Modelo.id == auto.modelo_id).first()
                print(f"  - {marca.nombre} {modelo.nombre} ({auto.anio}) - ${auto.precio}")
        
    finally:
        db.close()

if __name__ == "__main__":
    verify_data()
