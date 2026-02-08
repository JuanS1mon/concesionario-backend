from sqlalchemy.orm import Session, selectinload
from app.models.cotizacion import Cotizacion
from app.models.auto import Auto
from app.schemas.cotizacion import CotizacionCreate
from datetime import datetime

def crear_cotizacion(db: Session, cotizacion: CotizacionCreate):
    db_cot = Cotizacion(**cotizacion.dict(), fecha_creacion=datetime.utcnow())
    # Calcular score basado en completitud
    score = 0
    if cotizacion.telefono:
        score += 1
    if cotizacion.ciudad:
        score += 1
    if cotizacion.fuente:
        score += 1
    if cotizacion.preferencias_contacto:
        score += 1
    db_cot.score = score
    db_cot.estado_oportunidad = "Nuevo"  # Asegurar estado inicial
    db.add(db_cot)
    db.commit()
    db.refresh(db_cot)
    return db_cot

def listar_cotizaciones(db: Session):
    return db.query(Cotizacion).options(
        selectinload(Cotizacion.auto).selectinload(Auto.marca),
        selectinload(Cotizacion.auto).selectinload(Auto.modelo),
        selectinload(Cotizacion.auto).selectinload(Auto.estado),
        selectinload(Cotizacion.auto).selectinload(Auto.imagenes)
    ).all()
