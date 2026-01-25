import requests

# Probar endpoint raíz
response = requests.get("http://localhost:8001/")
print("Endpoint raíz:", response.json())

# Probar crear cotización
data = {
    "nombre_usuario": "Juan Pérez",
    "email": "juan@example.com",
    "telefono": "123456789",
    "auto_id": 1,
    "mensaje": "Estoy interesado en este auto"
}
response = requests.post("http://localhost:8001/cotizaciones/", json=data)
print("Crear cotización:", response.json())

# Probar listar cotizaciones
response = requests.get("http://localhost:8001/cotizaciones/")
print("Listar cotizaciones:", response.json())