from sqlalchemy.orm import Session
from app.models.auto import Auto
from app.schemas.auto import AutoCreate, AutoUpdate

def get_autos(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Auto).offset(skip).limit(limit).all()

def get_auto(db: Session, auto_id: int):
    return db.query(Auto).filter(Auto.id == auto_id).first()

def create_auto(db: Session, auto: AutoCreate):
    db_auto = Auto(**auto.model_dump())
    db.add(db_auto)
    db.commit()
    db.refresh(db_auto)
    return db_auto

def update_auto(db: Session, auto_id: int, auto: AutoUpdate):
    db_auto = db.query(Auto).filter(Auto.id == auto_id).first()
    if db_auto:
        update_data = auto.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_auto, field, value)
        db.commit()
        db.refresh(db_auto)
    return db_auto

def delete_auto(db: Session, auto_id: int):
    db_auto = db.query(Auto).filter(Auto.id == auto_id).first()
    if db_auto:
        db.delete(db_auto)
        db.commit()
    return db_auto