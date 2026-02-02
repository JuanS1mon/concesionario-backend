from sqlalchemy.orm import Session
from app.models.modelo import Modelo
from app.schemas.modelo import ModeloCreate, ModeloUpdate

def get_modelos(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Modelo).offset(skip).limit(limit).all()

def get_modelo(db: Session, modelo_id: int):
    return db.query(Modelo).filter(Modelo.id == modelo_id).first()

def create_modelo(db: Session, modelo: ModeloCreate):
    db_modelo = Modelo(**modelo.model_dump())
    db.add(db_modelo)
    db.commit()
    db.refresh(db_modelo)
    return db_modelo

def update_modelo(db: Session, modelo_id: int, modelo: ModeloUpdate):
    db_modelo = db.query(Modelo).filter(Modelo.id == modelo_id).first()
    if db_modelo:
        update_data = modelo.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_modelo, field, value)
        db.commit()
        db.refresh(db_modelo)
    return db_modelo

def get_modelos_by_marca(db: Session, marca_id: int):
    return db.query(Modelo).filter(Modelo.marca_id == marca_id).all()

def delete_modelo(db: Session, modelo_id: int):
    db_modelo = db.query(Modelo).filter(Modelo.id == modelo_id).first()
    if db_modelo:
        db.delete(db_modelo)
        db.commit()
    return db_modelo