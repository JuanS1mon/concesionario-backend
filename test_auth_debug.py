"""
Script para diagnosticar problemas de autenticación en PUT /autos/{id}
"""

import requests
import json

BASE_URL = "http://localhost:8004"

# Credenciales de admin
USERNAME = "juan@sysne.ar"
PASSWORD = "Admin123$"

print("="*70)
print("DIAGNÓSTICO DE AUTENTICACIÓN")
print("="*70)

# Step 1: Login para obtener token
print("\n[1] Intentando login...")
print(f"    Username: {USERNAME}")

response = requests.post(
    f"{BASE_URL}/auth/login",
    data={"username": USERNAME, "password": PASSWORD}
)

if response.status_code == 200:
    login_data = response.json()
    token = login_data.get('access_token')
    print(f"✅ Login exitoso")
    print(f"    Token: {token[:50]}...")
else:
    print(f"❌ Login fallido: {response.status_code}")
    print(f"    Response: {response.json()}")
    exit(1)

# Step 2: Intentar GET /autos/5 (debería funcionar sin auth)
print("\n[2] GET /autos/5 (sin autenticación)...")
response = requests.get(f"{BASE_URL}/autos/5")
if response.status_code == 200:
    print(f"✅ GET funciona sin autenticación")
else:
    print(f"❌ GET requiere autenticación: {response.status_code}")

# Step 3: Intentar PUT /autos/5 sin token
print("\n[3] PUT /autos/5 (sin token)...")
data = {
    "marca_id": 3,
    "modelo_id": 9,
    "anio": 2022,
    "tipo": "SUV",
    "precio": 40000,
    "descripcion": "Test sin token",
    "estado_id": 1,
    "en_stock": True
}
response = requests.put(f"{BASE_URL}/autos/5", json=data)
if response.status_code == 401:
    print(f"✅ Sin token → 401 (correcto)")
else:
    print(f"❌ Status inesperado: {response.status_code}")

# Step 4: Intentar PUT /autos/5 con token
print("\n[4] PUT /autos/5 (con token)...")
headers = {"Authorization": f"Bearer {token}"}
response = requests.put(f"{BASE_URL}/autos/5", json=data, headers=headers)
if response.status_code == 200:
    print(f"✅ PUT con token funcionó")
    print(f"    Auto actualizado: {response.json()['id']}")
elif response.status_code == 401:
    print(f"❌ PUT rechazado 401 incluso con token válido")
    print(f"    Response: {response.json()}")
else:
    print(f"❌ Error: {response.status_code}")
    print(f"    Response: {response.json()}")

# Step 5: Verificar estructura del token
print("\n[5] Verificando token...")
print(f"    Token tiene '{len(token)}' caracteres")
print(f"    Prefix: Bearer {token[:20]}...")

# Step 6: Test con header incorrecto
print("\n[6] Intentar PUT con header incorrecto (sin 'Bearer')...")
bad_headers = {"Authorization": token}
response = requests.put(f"{BASE_URL}/autos/5", json=data, headers=bad_headers)
print(f"    Status: {response.status_code} (debería ser 401/403)")

print("\n" + "="*70)
print("FIN DEL DIAGNÓSTICO")
print("="*70)
