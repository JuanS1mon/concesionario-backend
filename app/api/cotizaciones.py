from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.cotizacion import Cotizacion
from app.schemas.cotizacion import CotizacionCreate, CotizacionOut
from app.crud.cotizacion import crear_cotizacion as crud_crear_cotizacion, listar_cotizaciones as crud_listar_cotizaciones
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
    return crud_crear_cotizacion(db, cotizacion)

@router.get("/", response_model=list[CotizacionOut])
def listar_cotizaciones(db: Session = Depends(get_db)):
    return crud_listar_cotizaciones(db)

@router.get("/oportunidades", response_model=list[CotizacionOut])
def listar_oportunidades(estado: str = None, db: Session = Depends(get_db)):
    query = db.query(Cotizacion)
    if estado:
        query = query.filter(Cotizacion.estado_oportunidad == estado)
    return query.all()
