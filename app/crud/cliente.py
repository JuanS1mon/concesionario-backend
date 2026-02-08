from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.models.cliente import Cliente
from app.models.oportunidad import Oportunidad
from app.schemas.cliente import ClienteCreate, ClienteUpdate
from datetime import datetime


def calcular_score(cliente_data: dict) -> int:
    """Calcula score automático basado en completitud y calidad del lead."""
    score = 0
    if cliente_data.get("telefono"):
        score += 15
    if cliente_data.get("email"):
        score += 10
    if cliente_data.get("ciudad"):
        score += 5
    if cliente_data.get("fuente"):
        score += 5
    if cliente_data.get("preferencias_contacto"):
        score += 5
    if cliente_data.get("presupuesto_min") or cliente_data.get("presupuesto_max"):
        score += 20
    if cliente_data.get("tipo_vehiculo_interes"):
        score += 15
    if cliente_data.get("direccion"):
        score += 5
    # Fuentes de mayor calidad
    fuente = cliente_data.get("fuente", "")
    if fuente in ["referido", "recurrente"]:
        score += 20
    elif fuente in ["web", "cotizacion"]:
        score += 10
    return min(score, 100)


def determinar_calificacion(score: int) -> str:
    """Determina la calificación del lead basada en el score."""
    if score >= 60:
        return "caliente"
    elif score >= 30:
        return "tibio"
    return "frio"


def crear_cliente(db: Session, cliente: ClienteCreate):
    data = cliente.model_dump()
    score = calcular_score(data)
    calificacion = determinar_calificacion(score)

    db_cliente = Cliente(
        **data,
        score=score,
        calificacion=calificacion,
        fecha_creacion=datetime.utcnow(),
        fecha_actualizacion=datetime.utcnow()
    )
    db.add(db_cliente)
    db.commit()
    db.refresh(db_cliente)
    return db_cliente


def listar_clientes(db: Session, estado: str = None, calificacion: str = None, activo: bool = None, busqueda: str = None):
    query = db.query(Cliente)
    
    if estado:
        query = query.filter(Cliente.estado == estado)
    if calificacion:
        query = query.filter(Cliente.calificacion == calificacion)
    if activo is not None:
        query = query.filter(Cliente.activo == activo)
    if busqueda:
        search = f"%{busqueda}%"
        query = query.filter(
            (Cliente.nombre.ilike(search)) |
            (Cliente.apellido.ilike(search)) |
            (Cliente.email.ilike(search)) |
            (Cliente.telefono.ilike(search)) |
            (Cliente.ciudad.ilike(search))
        )
    
    return query.order_by(desc(Cliente.fecha_creacion)).all()


def obtener_cliente(db: Session, cliente_id: int):
    return db.query(Cliente).filter(Cliente.id == cliente_id).first()


def actualizar_cliente(db: Session, cliente_id: int, cliente_update: ClienteUpdate):
    db_cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not db_cliente:
        return None
    
    update_data = cliente_update.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_cliente, key, value)
    
    # Recalcular score si se actualizan datos relevantes
    cliente_dict = {c.name: getattr(db_cliente, c.name) for c in Cliente.__table__.columns}
    db_cliente.score = calcular_score(cliente_dict)
    db_cliente.calificacion = determinar_calificacion(db_cliente.score)
    db_cliente.fecha_actualizacion = datetime.utcnow()
    
    db.commit()
    db.refresh(db_cliente)
    return db_cliente


def eliminar_cliente(db: Session, cliente_id: int):
    db_cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not db_cliente:
        return False
    db.delete(db_cliente)
    db.commit()
    return True


def obtener_estadisticas_clientes(db: Session):
    """Estadísticas para el dashboard CRM."""
    total = db.query(func.count(Cliente.id)).scalar()
    nuevos = db.query(func.count(Cliente.id)).filter(Cliente.estado == "nuevo").scalar()
    contactados = db.query(func.count(Cliente.id)).filter(Cliente.estado == "contactado").scalar()
    calificados = db.query(func.count(Cliente.id)).filter(Cliente.estado == "calificado").scalar()
    clientes_activos = db.query(func.count(Cliente.id)).filter(Cliente.estado == "cliente").scalar()
    perdidos = db.query(func.count(Cliente.id)).filter(Cliente.estado == "perdido").scalar()
    
    # Por calificación
    frios = db.query(func.count(Cliente.id)).filter(Cliente.calificacion == "frio").scalar()
    tibios = db.query(func.count(Cliente.id)).filter(Cliente.calificacion == "tibio").scalar()
    calientes = db.query(func.count(Cliente.id)).filter(Cliente.calificacion == "caliente").scalar()
    
    # Score promedio
    score_promedio = db.query(func.avg(Cliente.score)).scalar() or 0
    
    return {
        "total": total,
        "por_estado": {
            "nuevo": nuevos,
            "contactado": contactados,
            "calificado": calificados,
            "cliente": clientes_activos,
            "perdido": perdidos
        },
        "por_calificacion": {
            "frio": frios,
            "tibio": tibios,
            "caliente": calientes
        },
        "score_promedio": round(score_promedio, 1)
    }
