import sys
import os
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models.admin import Admin
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return password

def create_admin(email, password, nombre_completo=None):
    db: Session = SessionLocal()
    if db.query(Admin).filter(Admin.email == email).first():
        print("El admin ya existe.")
        return
    hashed_password = get_password_hash(password)
    admin = Admin(email=email, hashed_password=hashed_password, nombre_completo=nombre_completo)
    db.add(admin)
    db.commit()
    print(f"Admin creado: {email}")

if __name__ == "__main__":
    email = sys.argv[1] if len(sys.argv) > 1 else "juan@sysne.ar"
    password = sys.argv[2] if len(sys.argv) > 2 else "Admin123$"
    nombre_completo = sys.argv[3] if len(sys.argv) > 3 else None
    create_admin(email, password, nombre_completo)
