from sqlalchemy.orm import Session
from app.models.admin import Admin
from app.schemas.admin import AdminCreate, AdminUpdate
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

def get_admin(db: Session, admin_id: int):
    return db.query(Admin).filter(Admin.id == admin_id).first()

def get_admin_by_email(db: Session, email: str):
    return db.query(Admin).filter(Admin.email == email).first()

def get_admins(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Admin).offset(skip).limit(limit).all()

def create_admin(db: Session, admin: AdminCreate):
    # Hash de la contraseña
    hashed_password = pwd_context.hash(admin.contrasena)

    db_admin = Admin(
        email=admin.email,
        hashed_password=hashed_password,
        nombre_completo=admin.nombre_completo
    )
    db.add(db_admin)
    db.commit()
    db.refresh(db_admin)
    return db_admin

def update_admin(db: Session, admin_id: int, admin: AdminUpdate):
    db_admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if db_admin:
        update_data = admin.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "contrasena":
                # Hash de la nueva contraseña
                value = pwd_context.hash(value)
            setattr(db_admin, field, value)
        db.commit()
        db.refresh(db_admin)
    return db_admin

def delete_admin(db: Session, admin_id: int):
    db_admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if db_admin:
        db.delete(db_admin)
        db.commit()
    return db_admin

def authenticate_admin(db: Session, email: str, password: str):
    admin = db.query(Admin).filter(Admin.email == email).first()
    if not admin:
        return False
    if not pwd_context.verify(password, admin.hashed_password):
        return False
    return admin