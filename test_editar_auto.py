"""
Script para probar que la página de edición de auto funciona correctamente.
Verifica que GET /imagenes/auto/{id} no devuelve error 500
"""

import requests
import json

BASE_URL = "http://localhost:8004"

# Get autos
print("="*60)
print("Obteniendo autos para probar edición...")
print("="*60)
response = requests.get(f"{BASE_URL}/autos/")
autos = response.json()

if autos:
    auto = autos[0]
    auto_id = auto['id']
    
    print(f"\nAuto seleccionado: ID={auto_id}")
    print(f"Marca: {auto['marca_id']}, Modelo: {auto['modelo_id']}")
    
    # Test endpoint GET /autos/{id}
    print("\n" + "="*60)
    print(f"TEST: GET /autos/{auto_id}")
    print("="*60)
    response = requests.get(f"{BASE_URL}/autos/{auto_id}")
    if response.status_code == 200:
        auto_data = response.json()
        print(f"✅ Auto obtenido correctamente")
        print(f"   Precio: ${auto_data['precio']}")
        print(f"   Tipo: {auto_data['tipo']}")
    else:
        print(f"❌ Error al obtener auto: {response.status_code}")
    
    # Test endpoint GET /imagenes/auto/{id} - Este era el que daba error
    print("\n" + "="*60)
    print(f"TEST: GET /imagenes/auto/{auto_id} (Este daba error 500)")
    print("="*60)
    response = requests.get(f"{BASE_URL}/imagenes/auto/{auto_id}")
    if response.status_code == 200:
        imagenes = response.json()
        print(f"✅ Imágenes obtenidas correctamente ({len(imagenes)} imágenes)")
        for i, img in enumerate(imagenes, 1):
            print(f"   {i}. URL: {img['url'][:50]}...")
            print(f"      public_id: {img.get('public_id', 'None')}")
    else:
        print(f"❌ Error al obtener imágenes: {response.status_code}")
        print(f"   Response: {response.text}")
    
    print("\n" + "="*60)
    print("✅ Prueba de edición completada")
    print("="*60)
else:
    print("No hay autos en la base de datos")
