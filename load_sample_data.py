"""
Script para limpiar y recargar datos de ejemplo
"""
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.marca import Marca
from app.models.modelo import Modelo
from app.models.auto import Auto
from app.models.estado import Estado
from app.models.imagen import Imagen

def clean_and_reload():
    """Limpia y recarga los datos de ejemplo"""
    db = SessionLocal()
    
    try:
        print("Limpiando datos existentes...")
        
        # Limpiar en orden inverso de dependencias
        db.query(Imagen).delete()
        db.query(Auto).delete()
        db.query(Modelo).delete()
        db.query(Marca).delete()
        
        db.commit()
        print("✓ Datos limpios")
        
        # Obtener o crear estado disponible
        estado = db.query(Estado).filter(Estado.nombre == "Disponible").first()
        if not estado:
            estado = Estado(nombre="Disponible")
            db.add(estado)
            db.commit()
        
        print("Cargando marcas y modelos...")
        
        # Datos de marcas y modelos
        marcas_datos = {
            "Toyota": ["Corolla", "Camry", "RAV4", "Highlander", "Prius"],
            "Honda": ["Civic", "Accord", "CR-V", "Pilot", "Fit"],
            "Ford": ["Focus", "Mustang", "Escape", "Explorer", "F-150"],
            "Chevrolet": ["Cruze", "Malibu", "Equinox", "Traverse", "Colorado"],
            "Nissan": ["Altima", "Sentra", "Rogue", "Murano", "Maxima"],
            "BMW": ["Serie 3", "Serie 5", "X3", "X5", "Z4"],
            "Mercedes-Benz": ["C-Class", "E-Class", "GLC", "GLE", "AMG GT"],
            "Volkswagen": ["Golf", "Jetta", "Passat", "Tiguan", "Beetle"],
            "Hyundai": ["Elantra", "Sonata", "Santa Fe", "Tucson", "Ioniq"],
            "Kia": ["Forte", "Optima", "Sportage", "Sorento", "Niro"],
        }
        
        # Crear marcas y modelos
        marcas_obj = {}
        modelos_obj = {}
        
        for marca_nombre, modelos in marcas_datos.items():
            # Crear marca
            marca = Marca(nombre=marca_nombre)
            db.add(marca)
            db.flush()
            marcas_obj[marca_nombre] = marca
            
            # Crear modelos para esta marca
            for modelo_nombre in modelos:
                modelo = Modelo(nombre=modelo_nombre, marca_id=marca.id)
                db.add(modelo)
                db.flush()
                modelos_obj[f"{marca_nombre}_{modelo_nombre}"] = modelo
        
        db.commit()
        print(f"✓ {len(marcas_obj)} marcas creadas")
        print(f"✓ {len(modelos_obj)} modelos creados")
        
        print("Cargando 15 autos de ejemplo...")
        
        # Crear 15 autos de ejemplo
        autos_ejemplos = [
            {"marca": "Toyota", "modelo": "Corolla", "anio": 2023, "tipo": "Sedan", "precio": 25000.00, "descripcion": "Toyota Corolla 2023, excelente condición, bajo kilometraje"},
            {"marca": "Toyota", "modelo": "Camry", "anio": 2022, "tipo": "Sedan", "precio": 32000.00, "descripcion": "Toyota Camry 2022, automático, aire acondicionado"},
            {"marca": "Honda", "modelo": "Civic", "anio": 2023, "tipo": "Sedan", "precio": 26500.00, "descripcion": "Honda Civic 2023, deportivo, perfectas condiciones"},
            {"marca": "Honda", "modelo": "CR-V", "anio": 2022, "tipo": "SUV", "precio": 35000.00, "descripcion": "Honda CR-V 2022, SUV compacto, 4x4"},
            {"marca": "Ford", "modelo": "Focus", "anio": 2021, "tipo": "Hatchback", "precio": 22000.00, "descripcion": "Ford Focus 2021, gasolina, mantenimiento al día"},
            {"marca": "Ford", "modelo": "Mustang", "anio": 2023, "tipo": "Coupe", "precio": 48000.00, "descripcion": "Ford Mustang 2023, deportivo de lujo, motor V8"},
            {"marca": "Chevrolet", "modelo": "Cruze", "anio": 2022, "tipo": "Sedan", "precio": 23500.00, "descripcion": "Chevrolet Cruze 2022, económico, bajo consumo"},
            {"marca": "Chevrolet", "modelo": "Equinox", "anio": 2023, "tipo": "SUV", "precio": 38000.00, "descripcion": "Chevrolet Equinox 2023, SUV moderna, segura"},
            {"marca": "Nissan", "modelo": "Altima", "anio": 2022, "tipo": "Sedan", "precio": 28000.00, "descripcion": "Nissan Altima 2022, transmisión automática, aire acondicionado"},
            {"marca": "Nissan", "modelo": "Rogue", "anio": 2023, "tipo": "SUV", "precio": 33000.00, "descripcion": "Nissan Rogue 2023, compacta, buena tracción"},
            {"marca": "BMW", "modelo": "Serie 3", "anio": 2022, "tipo": "Sedan", "precio": 55000.00, "descripcion": "BMW Serie 3 2022, lujo y desempeño, cuero"},
            {"marca": "Mercedes-Benz", "modelo": "C-Class", "anio": 2023, "tipo": "Sedan", "precio": 60000.00, "descripcion": "Mercedes-Benz C-Class 2023, premium, motor eficiente"},
            {"marca": "Volkswagen", "modelo": "Golf", "anio": 2022, "tipo": "Hatchback", "precio": 27000.00, "descripcion": "Volkswagen Golf 2022, clásico deportivo, confiable"},
            {"marca": "Hyundai", "modelo": "Elantra", "anio": 2023, "tipo": "Sedan", "precio": 21000.00, "descripcion": "Hyundai Elantra 2023, económico, garantía"},
            {"marca": "Kia", "modelo": "Sportage", "anio": 2023, "tipo": "SUV", "precio": 31000.00, "descripcion": "Kia Sportage 2023, SUV compacta, diseño moderno"},
        ]
        
        autos_creados = 0
        for auto_data in autos_ejemplos:
            marca_key = f"{auto_data['marca']}_{auto_data['modelo']}"
            if marca_key in modelos_obj:
                auto = Auto(
                    marca_id=marcas_obj[auto_data['marca']].id,
                    modelo_id=modelos_obj[marca_key].id,
                    anio=auto_data['anio'],
                    tipo=auto_data['tipo'],
                    precio=auto_data['precio'],
                    descripcion=auto_data['descripcion'],
                    en_stock=True,
                    estado_id=estado.id
                )
                db.add(auto)
                autos_creados += 1
        
        db.commit()
        print(f"✓ {autos_creados} autos creados")
        print("\n✅ ¡Datos recargados exitosamente!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    clean_and_reload()
