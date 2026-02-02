"""
Script para verificar las imágenes de los autos en la base de datos
"""
import sys
import os

# Agregar el directorio padre al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database import SessionLocal
from app.models.auto import Auto
from app.models.imagen import Imagen
from app.models.marca import Marca
from app.models.modelo import Modelo

db = SessionLocal()

try:
    print("\n=== Verificando Autos e Imágenes ===\n")
    
    autos = db.query(Auto).all()
    print(f"Total de autos: {len(autos)}\n")
    
    for auto in autos[:5]:  # Mostrar solo los primeros 5
        marca = db.query(Marca).filter(Marca.id == auto.marca_id).first()
        modelo = db.query(Modelo).filter(Modelo.id == auto.modelo_id).first()
        imagenes = db.query(Imagen).filter(Imagen.auto_id == auto.id).all()
        
        print(f"Auto ID: {auto.id}")
        print(f"  Marca/Modelo: {marca.nombre if marca else 'N/A'} {modelo.nombre if modelo else 'N/A'}")
        print(f"  Año: {auto.anio}")
        print(f"  Precio: ${auto.precio}")
        print(f"  Cantidad de imágenes: {len(imagenes)}")
        
        if imagenes:
            for i, img in enumerate(imagenes, 1):
                print(f"    Imagen {i}: {img.url[:80]}..." if len(img.url) > 80 else f"    Imagen {i}: {img.url}")
        else:
            print(f"    Sin imágenes asociadas")
        print()
    
    # Contar autos sin imágenes
    autos_sin_imagenes = 0
    for auto in autos:
        imagenes = db.query(Imagen).filter(Imagen.auto_id == auto.id).all()
        if not imagenes:
            autos_sin_imagenes += 1
    
    print(f"\n📊 Estadísticas:")
    print(f"  Autos sin imágenes: {autos_sin_imagenes} de {len(autos)}")
    
finally:
    db.close()
