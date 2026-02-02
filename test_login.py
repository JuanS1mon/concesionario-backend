import requests

# Probar el login
response = requests.post('http://localhost:8000/auth/login', data={
    'username': 'juan@sysne.ar',
    'password': 'Admin123$'
})

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
