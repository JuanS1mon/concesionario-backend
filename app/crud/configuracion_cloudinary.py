from sqlalchemy.orm import Session
from app.models.configuracion_cloudinary import ConfiguracionCloudinary
from app.schemas.configuracion_cloudinary import ConfiguracionCloudinaryCreate, ConfiguracionCloudinaryUpdate

def get_configuracion_cloudinary(db: Session):
    return db.query(ConfiguracionCloudinary).filter(ConfiguracionCloudinary.activo == True).first()

def create_configuracion_cloudinary(db: Session, configuracion: ConfiguracionCloudinaryCreate):
    # Desactivar configuraciones anteriores
    db.query(ConfiguracionCloudinary).update({"activo": False})
    
    db_configuracion = ConfiguracionCloudinary(**configuracion.model_dump())
    db.add(db_configuracion)
    db.commit()
    db.refresh(db_configuracion)
    return db_configuracion

def update_configuracion_cloudinary(db: Session, configuracion_id: int, configuracion: ConfiguracionCloudinaryUpdate):
    db_configuracion = db.query(ConfiguracionCloudinary).filter(ConfiguracionCloudinary.id == configuracion_id).first()
    if db_configuracion:
        update_data = configuracion.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_configuracion, field, value)
        db.commit()
        db.refresh(db_configuracion)
    return db_configuracion

def delete_configuracion_cloudinary(db: Session, configuracion_id: int):
    db_configuracion = db.query(ConfiguracionCloudinary).filter(ConfiguracionCloudinary.id == configuracion_id).first()
    if db_configuracion:
        db.delete(db_configuracion)
        db.commit()
    return db_configuracion