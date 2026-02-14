from sqlalchemy.orm import Session
from app.models.configuracion_ai import ConfiguracionAI
from app.schemas.configuracion_ai import ConfiguracionAICreate, ConfiguracionAIUpdate


def get_configuracion_ai(db: Session):
    return db.query(ConfiguracionAI).filter(ConfiguracionAI.activo == True).first()


def create_configuracion_ai(db: Session, configuracion: ConfiguracionAICreate):
    db.query(ConfiguracionAI).update({"activo": False})
    db_config = ConfiguracionAI(**configuracion.model_dump())
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config


def update_configuracion_ai(db: Session, configuracion_id: int, configuracion: ConfiguracionAIUpdate):
    db_config = db.query(ConfiguracionAI).filter(ConfiguracionAI.id == configuracion_id).first()
    if db_config:
        update_data = configuracion.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_config, field, value)
        db.commit()
        db.refresh(db_config)
    return db_config


def delete_configuracion_ai(db: Session, configuracion_id: int):
    db_config = db.query(ConfiguracionAI).filter(ConfiguracionAI.id == configuracion_id).first()
    if db_config:
        db.delete(db_config)
        db.commit()
    return db_config
