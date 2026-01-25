from sqlalchemy.orm import Session
from app.models.imagen import Imagen
from app.schemas.imagen import ImagenCreate

def get_imagenes_by_auto(db: Session, auto_id: int):
    return db.query(Imagen).filter(Imagen.auto_id == auto_id).all()

def create_imagen(db: Session, imagen: ImagenCreate):
    db_imagen = Imagen(**imagen.model_dump())
    db.add(db_imagen)
    db.commit()
    db.refresh(db_imagen)
    return db_imagen

def delete_imagen(db: Session, imagen_id: int):
    db_imagen = db.query(Imagen).filter(Imagen.id == imagen_id).first()
    if db_imagen:
        db.delete(db_imagen)
        db.commit()
    return db_imagen