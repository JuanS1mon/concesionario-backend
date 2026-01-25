from sqlalchemy.orm import Session
from app.models.marca import Marca
from app.schemas.marca import MarcaCreate, MarcaUpdate

def get_marcas(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Marca).offset(skip).limit(limit).all()

def get_marca(db: Session, marca_id: int):
    return db.query(Marca).filter(Marca.id == marca_id).first()

def create_marca(db: Session, marca: MarcaCreate):
    db_marca = Marca(**marca.model_dump())
    db.add(db_marca)
    db.commit()
    db.refresh(db_marca)
    return db_marca

def update_marca(db: Session, marca_id: int, marca: MarcaUpdate):
    db_marca = db.query(Marca).filter(Marca.id == marca_id).first()
    if db_marca:
        update_data = marca.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_marca, field, value)
        db.commit()
        db.refresh(db_marca)
    return db_marca

def delete_marca(db: Session, marca_id: int):
    db_marca = db.query(Marca).filter(Marca.id == marca_id).first()
    if db_marca:
        db.delete(db_marca)
        db.commit()
    return db_marca