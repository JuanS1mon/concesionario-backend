"""
Script para simular exactamente cómo el frontend hace login y luego PUT
Verifica si hay un problema en cómo se envían los datos en el frontend
"""

import requests
from urllib.parse import urlencode

BASE_URL = "http://localhost:8004"
USERNAME = "juan@sysne.ar"
PASSWORD = "Admin123$"

print("="*70)
print("SIMULACIÓN DEL FLUJO DEL FRONTEND")
print("="*70)

# Simular el método fetch del frontend para login
print("\n[1] Simulating frontend login (como lo hace Next.js)...")
print(f"    Content-Type: application/x-www-form-urlencoded")
print(f"    Body: username={USERNAME}&password={PASSWORD}")

# El frontend usa URLSearchParams
body = urlencode({"username": USERNAME, "password": PASSWORD})

response = requests.post(
    f"{BASE_URL}/auth/login",
    data=body,
    headers={"Content-Type": "application/x-www-form-urlencoded"}
)

if response.status_code == 200:
    token = response.json().get("access_token")
    print(f"✅ Login exitoso")
    print(f"    Token guardado en localStorage")
    print(f"    Token: {token[:50]}...")
else:
    print(f"❌ Login fallido: {response.status_code}")
    print(f"    Response: {response.json()}")
    exit(1)

# Ahora simular el PUT del frontend
print("\n[2] Simulando PUT /autos/5 (como lo hace la página editar)...")

# Esto es exactamente lo que hace el frontend
headers = {
    'Content-Type': 'application/json',
}
if token:
    headers['Authorization'] = f'Bearer {token}'

autoData = {
    "marca_id": 3,
    "modelo_id": 9,
    "estado_id": 1,
    "anio": 2022,
    "precio": 40000,
    "tipo": "SUV",
    "descripcion": "Test desde script",
    "en_stock": True,
}

print(f"    Headers:")
print(f"      Content-Type: application/json")
print(f"      Authorization: Bearer {token[:50]}...")

response = requests.put(
    f"{BASE_URL}/autos/5",
    json=autoData,
    headers=headers
)

if response.status_code == 200:
    print(f"✅ PUT exitoso")
    updated_auto = response.json()
    print(f"    Auto actualizado: ID={updated_auto['id']}, Descripcion={updated_auto['descripcion']}")
elif response.status_code == 401:
    print(f"❌ PUT rechazado con 401 Unauthorized")
    print(f"    Response: {response.json()}")
else:
    print(f"❌ Error: {response.status_code}")
    print(f"    Response: {response.json()}")

print("\n" + "="*70)
print("CONCLUSIÓN:")
print("="*70)
if response.status_code == 200:
    print("✅ El backend está funcionando correctamente")
    print("❓ El problema está en cómo el FRONTEND está enviando el token")
    print("   Posibles causas:")
    print("   - Token no se está guardando en localStorage")
    print("   - Token no se está leyendo de localStorage") 
    print("   - Headers no se están enviando correctamente")
else:
    print("❌ El backend tiene un problema")
