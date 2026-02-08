from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func, desc
from app.models.oportunidad import Oportunidad
from app.models.cliente import Cliente
from app.models.auto import Auto
from app.schemas.oportunidad import OportunidadCreate, OportunidadUpdate
from datetime import datetime


ETAPA_PROBABILIDAD = {
    "prospecto": 10,
    "contacto": 20,
    "evaluacion": 40,
    "negociacion": 60,
    "cierre": 80,
    "ganada": 100,
    "perdida": 0
}


def crear_oportunidad(db: Session, oportunidad: OportunidadCreate):
    data = oportunidad.model_dump()
    
    # Asignar probabilidad según etapa si no se proporcionó
    if data.get("etapa") and data.get("probabilidad") == 10:
        data["probabilidad"] = ETAPA_PROBABILIDAD.get(data["etapa"], 10)
    
    db_oportunidad = Oportunidad(
        **data,
        fecha_creacion=datetime.utcnow(),
        fecha_actualizacion=datetime.utcnow()
    )
    db.add(db_oportunidad)
    db.commit()
    db.refresh(db_oportunidad)
    return db_oportunidad


def listar_oportunidades(db: Session, etapa: str = None, prioridad: str = None, cliente_id: int = None):
    query = db.query(Oportunidad).options(
        selectinload(Oportunidad.cliente),
        selectinload(Oportunidad.auto).selectinload(Auto.marca),
        selectinload(Oportunidad.auto).selectinload(Auto.modelo),
        selectinload(Oportunidad.auto).selectinload(Auto.imagenes)
    )
    
    if etapa:
        query = query.filter(Oportunidad.etapa == etapa)
    if prioridad:
        query = query.filter(Oportunidad.prioridad == prioridad)
    if cliente_id:
        query = query.filter(Oportunidad.cliente_id == cliente_id)
    
    return query.order_by(desc(Oportunidad.fecha_creacion)).all()


def obtener_oportunidad(db: Session, oportunidad_id: int):
    return db.query(Oportunidad).options(
        selectinload(Oportunidad.cliente),
        selectinload(Oportunidad.auto).selectinload(Auto.marca),
        selectinload(Oportunidad.auto).selectinload(Auto.modelo),
        selectinload(Oportunidad.auto).selectinload(Auto.imagenes)
    ).filter(Oportunidad.id == oportunidad_id).first()


def actualizar_oportunidad(db: Session, oportunidad_id: int, oportunidad_update: OportunidadUpdate):
    db_oportunidad = db.query(Oportunidad).filter(Oportunidad.id == oportunidad_id).first()
    if not db_oportunidad:
        return None
    
    update_data = oportunidad_update.model_dump(exclude_unset=True)
    
    # Actualizar probabilidad automáticamente si cambia la etapa
    if "etapa" in update_data:
        nueva_etapa = update_data["etapa"]
        if "probabilidad" not in update_data:
            update_data["probabilidad"] = ETAPA_PROBABILIDAD.get(nueva_etapa, db_oportunidad.probabilidad)
        
        # Si pasa a ganada/perdida, registrar fecha de cierre
        if nueva_etapa in ["ganada", "perdida"] and not db_oportunidad.fecha_cierre:
            update_data["fecha_cierre"] = datetime.utcnow()
    
    for key, value in update_data.items():
        setattr(db_oportunidad, key, value)
    
    db_oportunidad.fecha_actualizacion = datetime.utcnow()
    db.commit()
    db.refresh(db_oportunidad)
    return db_oportunidad


def eliminar_oportunidad(db: Session, oportunidad_id: int):
    db_oportunidad = db.query(Oportunidad).filter(Oportunidad.id == oportunidad_id).first()
    if not db_oportunidad:
        return False
    db.delete(db_oportunidad)
    db.commit()
    return True


def obtener_estadisticas_oportunidades(db: Session):
    """Estadísticas para el dashboard CRM."""
    total = db.query(func.count(Oportunidad.id)).scalar()
    
    # Por etapa
    etapas = {}
    for etapa in ["prospecto", "contacto", "evaluacion", "negociacion", "cierre", "ganada", "perdida"]:
        etapas[etapa] = db.query(func.count(Oportunidad.id)).filter(Oportunidad.etapa == etapa).scalar()
    
    # Valor total del pipeline (excluyendo ganadas y perdidas)
    valor_pipeline = db.query(func.sum(Oportunidad.valor_estimado)).filter(
        Oportunidad.etapa.notin_(["ganada", "perdida"])
    ).scalar() or 0
    
    # Valor ganado
    valor_ganado = db.query(func.sum(Oportunidad.valor_estimado)).filter(
        Oportunidad.etapa == "ganada"
    ).scalar() or 0
    
    # Tasa de conversión
    ganadas = etapas.get("ganada", 0)
    cerradas = ganadas + etapas.get("perdida", 0)
    tasa_conversion = round((ganadas / cerradas * 100), 1) if cerradas > 0 else 0
    
    # Por prioridad
    prioridades = {}
    for prioridad in ["baja", "media", "alta", "urgente"]:
        prioridades[prioridad] = db.query(func.count(Oportunidad.id)).filter(
            Oportunidad.prioridad == prioridad
        ).scalar()
    
    return {
        "total": total,
        "por_etapa": etapas,
        "por_prioridad": prioridades,
        "valor_pipeline": valor_pipeline,
        "valor_ganado": valor_ganado,
        "tasa_conversion": tasa_conversion
    }
