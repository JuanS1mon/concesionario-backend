from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.cotizacion import Cotizacion
from app.schemas.cotizacion import CotizacionCreate, CotizacionOut
from app.crud.cotizacion import crear_cotizacion as crud_crear_cotizacion, listar_cotizaciones as crud_listar_cotizaciones
from datetime import datetime
import requests

router = APIRouter(prefix="/cotizaciones", tags=["cotizaciones"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=CotizacionOut)
def crear_cotizacion(cotizacion: CotizacionCreate, request: Request, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else None
    ubicacion = None
    if ip and ip != '127.0.0.1' and not ip.startswith('192.168.') and not ip.startswith('10.'):
        try:
            response = requests.get(f'https://ipapi.co/{ip}/json/', timeout=5)
            if response.status_code == 200:
                data = response.json()
                ubicacion = f"{data.get('city', '')}, {data.get('region', '')}, {data.get('country_name', '')}".strip(', ')
        except:
            pass
    cotizacion.ip = ip
    cotizacion.ubicacion = ubicacion
    return crud_crear_cotizacion(db, cotizacion)

@router.get("/", response_model=list[CotizacionOut])
def listar_cotizaciones(db: Session = Depends(get_db)):
    return crud_listar_cotizaciones(db)

@router.put("/{cotizacion_id}", response_model=CotizacionOut)
def actualizar_cotizacion(cotizacion_id: int, cotizacion_update: dict, db: Session = Depends(get_db)):
    cotizacion = db.query(Cotizacion).filter(Cotizacion.id == cotizacion_id).first()
    if not cotizacion:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")
    for key, value in cotizacion_update.items():
        setattr(cotizacion, key, value)
    db.commit()
    db.refresh(cotizacion)
    return cotizacion
