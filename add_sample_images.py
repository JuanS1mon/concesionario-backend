"""
Script para agregar imágenes de ejemplo a los autos
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

# URLs de imágenes de ejemplo de autos (Unsplash)
IMAGENES_EJEMPLO = {
    'Sedan': [
        'https://images.unsplash.com/photo-1555215695-3004980ad54e?w=800',
        'https://images.unsplash.com/photo-1552519507-da3b142c6e3d?w=800',
        'https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?w=800',
    ],
    'SUV': [
        'https://images.unsplash.com/photo-1519641471654-76ce0107ad1b?w=800',
        'https://images.unsplash.com/photo-1606664515524-ed2f786a0bd6?w=800',
        'https://images.unsplash.com/photo-1533473359331-0135ef1b58bf?w=800',
    ],
    'Coupe': [
        'https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=800',
        'https://images.unsplash.com/photo-1542362567-b07e54358753?w=800',
        'https://images.unsplash.com/photo-1525609004556-c46c7d6cf023?w=800',
    ],
    'Hatchback': [
        'https://images.unsplash.com/photo-1552519507-da3b142c6e3d?w=800',
        'https://images.unsplash.com/photo-1494976388531-d1058494cdd8?w=800',
        'https://images.unsplash.com/photo-1583121274602-3e2820c69888?w=800',
    ],
    'Default': [
        'https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?w=800',
        'https://images.unsplash.com/photo-1511919884226-fd3cad34687c?w=800',
        'https://images.unsplash.com/photo-1550355291-bbee04a92027?w=800',
    ]
}

def add_sample_images():
    """Agrega imágenes de ejemplo a todos los autos sin imágenes"""
    db = SessionLocal()
    
    try:
        print("🖼️  Agregando imágenes de ejemplo a los autos...\n")
        
        autos = db.query(Auto).all()
        imagenes_agregadas = 0
        
        for auto in autos:
            # Verificar si ya tiene imágenes
            imagenes_existentes = db.query(Imagen).filter(Imagen.auto_id == auto.id).all()
            
            if imagenes_existentes:
                print(f"⏭️  Auto ID {auto.id} ya tiene imágenes, omitiendo...")
                continue
            
            # Obtener marca y modelo para mostrar info
            marca = db.query(Marca).filter(Marca.id == auto.marca_id).first()
            modelo = db.query(Modelo).filter(Modelo.id == auto.modelo_id).first()
            
            # Seleccionar imágenes según el tipo de auto
            tipo = auto.tipo if auto.tipo in IMAGENES_EJEMPLO else 'Default'
            urls = IMAGENES_EJEMPLO[tipo]
            
            print(f"📸 Agregando imágenes a: {marca.nombre} {modelo.nombre} ({auto.anio})")
            
            # Agregar 2-3 imágenes por auto
            for i, url in enumerate(urls[:3], 1):
                imagen = Imagen(
                    url=url,
                    auto_id=auto.id
                )
                db.add(imagen)
                imagenes_agregadas += 1
                print(f"  ✓ Imagen {i} agregada")
            
            print()
        
        db.commit()
        print(f"\n✅ ¡Completado! Se agregaron {imagenes_agregadas} imágenes a {len(autos)} autos")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    add_sample_images()
