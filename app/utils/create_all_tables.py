from app.database import Base, engine
import app.models  # Importa todos los modelos para registrarlos en Base

if __name__ == "__main__":
    print("Creando todas las tablas en la base de datos...")
    Base.metadata.create_all(bind=engine)
    print("¡Tablas creadas!")
