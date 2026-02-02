import sys
import os

# Agregar el directorio padre al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.admin import Admin

db = SessionLocal()

# Eliminar todos los admins existentes
db.query(Admin).delete()
db.commit()

print("✓ Todos los admins han sido eliminados")
db.close()
