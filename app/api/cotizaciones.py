from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.cotizacion import Cotizacion
from app.schemas.cotizacion import CotizacionCreate, CotizacionOut
from datetime import datetime

router = APIRouter(prefix="/cotizaciones", tags=["cotizaciones"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=CotizacionOut)
def crear_cotizacion(cotizacion: CotizacionCreate, db: Session = Depends(get_db)):
    db_cot = Cotizacion(**cotizacion.dict(), fecha_creacion=datetime.utcnow())
    db.add(db_cot)
    db.commit()
    db.refresh(db_cot)
    return db_cot

@router.get("/", response_model=list[CotizacionOut])
def listar_cotizaciones(db: Session = Depends(get_db)):
    return db.query(Cotizacion).all()
