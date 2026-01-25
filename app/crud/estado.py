from sqlalchemy.orm import Session
from app.models.estado import Estado
from app.schemas.estado import EstadoCreate, EstadoUpdate

def get_estados(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Estado).offset(skip).limit(limit).all()

def get_estado(db: Session, estado_id: int):
    return db.query(Estado).filter(Estado.id == estado_id).first()

def create_estado(db: Session, estado: EstadoCreate):
    db_estado = Estado(**estado.model_dump())
    db.add(db_estado)
    db.commit()
    db.refresh(db_estado)
    return db_estado

def update_estado(db: Session, estado_id: int, estado: EstadoUpdate):
    db_estado = db.query(Estado).filter(Estado.id == estado_id).first()
    if db_estado:
        update_data = estado.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_estado, field, value)
        db.commit()
        db.refresh(db_estado)
    return db_estado

def delete_estado(db: Session, estado_id: int):
    db_estado = db.query(Estado).filter(Estado.id == estado_id).first()
    if db_estado:
        db.delete(db_estado)
        db.commit()
    return db_estado