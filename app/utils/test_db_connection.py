from app.database import engine

try:
    with engine.connect() as conn:
        result = conn.execute("SELECT 1")
        print("Conexión a PostgreSQL exitosa.")
except Exception as e:
    print(f"Error de conexión: {e}")
