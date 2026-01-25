from sqlalchemy.orm import Session
from app.models.cotizacion import Cotizacion
from app.schemas.cotizacion import CotizacionCreate
from datetime import datetime

def crear_cotizacion(db: Session, cotizacion: CotizacionCreate):
    db_cot = Cotizacion(**cotizacion.dict(), fecha_creacion=datetime.utcnow())
    db.add(db_cot)
    db.commit()
    db.refresh(db_cot)
    return db_cot

def listar_cotizaciones(db: Session):
    return db.query(Cotizacion).all()
