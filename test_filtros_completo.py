"""
Script para probar los filtros de autos después de la corrección.
Prueba que modelo_id ahora filtra correctamente.
"""

import requests
import json

BASE_URL = "http://localhost:8004"

# Test 1: Get all autos
print("="*60)
print("TEST 1: Obtener todos los autos (sin filtros)")
print("="*60)
response = requests.get(f"{BASE_URL}/autos/")
autos = response.json()
print(f"Total de autos: {len(autos)}")
if autos:
    print(f"\nPrimeros 3 autos:")
    for auto in autos[:3]:
        print(f"  - Auto {auto['id']}: marca_id={auto['marca_id']}, modelo_id={auto['modelo_id']}")

# Test 2: Filter by marca_id
print("\n" + "="*60)
print("TEST 2: Filtrar por marca_id=3 (Honda)")
print("="*60)
response = requests.get(f"{BASE_URL}/autos/", params={"marca_id": 3})
autos_marca = response.json()
print(f"Autos con marca_id=3: {len(autos_marca)}")
for auto in autos_marca:
    print(f"  - Auto {auto['id']}: marca_id={auto['marca_id']}, modelo_id={auto['modelo_id']}")

# Test 3: Filter by marca_id and modelo_id
if autos_marca:
    modelo_id = autos_marca[0]['modelo_id']
    print("\n" + "="*60)
    print(f"TEST 3: Filtrar por marca_id=3 Y modelo_id={modelo_id}")
    print("="*60)
    response = requests.get(
        f"{BASE_URL}/autos/",
        params={"marca_id": 3, "modelo_id": modelo_id}
    )
    autos_filtrados = response.json()
    print(f"Autos con marca_id=3 Y modelo_id={modelo_id}: {len(autos_filtrados)}")
    for auto in autos_filtrados:
        print(f"  - Auto {auto['id']}: marca_id={auto['marca_id']}, modelo_id={auto['modelo_id']}")

# Test 4: Test image schema fix
print("\n" + "="*60)
print("TEST 4: Probar que las imágenes se devuelven sin error (public_id opcional)")
print("="*60)
if autos:
    auto_id = autos[0]['id']
    response = requests.get(f"{BASE_URL}/imagenes/auto/{auto_id}")
    if response.status_code == 200:
        imagenes = response.json()
        print(f"✅ Auto {auto_id} tiene {len(imagenes)} imágenes")
        if imagenes:
            print(f"   Primera imagen: url={imagenes[0]['url']}, public_id={imagenes[0].get('public_id', 'None')}")
    else:
        print(f"❌ Error al obtener imágenes: {response.status_code}")
        print(response.text)

print("\n" + "="*60)
print("RESUMEN DE PRUEBAS")
print("="*60)
print("✅ Si ves resultados en todos los tests, los filtros funcionan correctamente")
