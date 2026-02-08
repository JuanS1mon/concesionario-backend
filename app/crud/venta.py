from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func, desc, extract
from app.models.venta import Venta
from app.models.auto import Auto
from app.models.estado import Estado
from app.models.oportunidad import Oportunidad
from app.schemas.venta import VentaCreate, VentaUpdate
from datetime import datetime


def _get_or_create_estado(db: Session, nombre: str) -> Estado:
    """Busca un estado por nombre o lo crea si no existe."""
    estado = db.query(Estado).filter(Estado.nombre == nombre).first()
    if not estado:
        estado = Estado(nombre=nombre)
        db.add(estado)
        db.flush()
    return estado


def _load_venta_relations(query):
    """Aplica selectinload para todas las relaciones de Venta."""
    return query.options(
        selectinload(Venta.cliente),
        selectinload(Venta.auto_vendido).selectinload(Auto.marca),
        selectinload(Venta.auto_vendido).selectinload(Auto.modelo),
        selectinload(Venta.auto_vendido).selectinload(Auto.estado),
        selectinload(Venta.auto_vendido).selectinload(Auto.imagenes),
        selectinload(Venta.auto_tomado).selectinload(Auto.marca),
        selectinload(Venta.auto_tomado).selectinload(Auto.modelo),
        selectinload(Venta.auto_tomado).selectinload(Auto.estado),
        selectinload(Venta.auto_tomado).selectinload(Auto.imagenes),
        selectinload(Venta.cotizacion),
        selectinload(Venta.oportunidad),
    )


def crear_venta(db: Session, venta: VentaCreate):
    data = venta.model_dump(exclude={"auto_tomado_data"})

    # --- Auto tomado: crear nuevo auto si se proporcionan datos ---
    auto_tomado_data = venta.auto_tomado_data
    if auto_tomado_data:
        estado_no_disponible = _get_or_create_estado(db, "No Disponible")
        nuevo_auto = Auto(
            marca_id=auto_tomado_data.marca_id,
            modelo_id=auto_tomado_data.modelo_id,
            anio=auto_tomado_data.anio,
            tipo=auto_tomado_data.tipo,
            precio=auto_tomado_data.precio,
            descripcion=auto_tomado_data.descripcion,
            en_stock=True,
            estado_id=estado_no_disponible.id,
        )
        db.add(nuevo_auto)
        db.flush()  # para obtener el ID
        data["auto_tomado_id"] = nuevo_auto.id

        # Si no se indicó precio_toma explícitamente, usar el precio del auto
        if data.get("precio_toma") is None:
            data["precio_toma"] = auto_tomado_data.precio

    # --- Auto vendido: marcar como vendido ---
    auto_vendido = db.query(Auto).filter(Auto.id == data["auto_vendido_id"]).first()
    if auto_vendido:
        estado_vendido = _get_or_create_estado(db, "Vendido")
        auto_vendido.en_stock = False
        auto_vendido.estado_id = estado_vendido.id

    # --- Calcular diferencia ---
    precio_venta = data["precio_venta"]
    precio_toma = data.get("precio_toma")
    if precio_toma is not None:
        data["diferencia"] = precio_venta - precio_toma
    else:
        data["diferencia"] = None

    # --- Si hay oportunidad vinculada, marcarla como ganada ---
    if data.get("oportunidad_id"):
        oportunidad = db.query(Oportunidad).filter(
            Oportunidad.id == data["oportunidad_id"]
        ).first()
        if oportunidad and oportunidad.etapa not in ["ganada", "perdida"]:
            oportunidad.etapa = "ganada"
            oportunidad.probabilidad = 100
            oportunidad.fecha_cierre = datetime.utcnow()
            oportunidad.fecha_actualizacion = datetime.utcnow()

    # --- Fecha de venta por defecto ---
    if not data.get("fecha_venta"):
        data["fecha_venta"] = datetime.utcnow()

    db_venta = Venta(
        **data,
        fecha_creacion=datetime.utcnow(),
        fecha_actualizacion=datetime.utcnow(),
    )
    db.add(db_venta)
    db.commit()
    db.refresh(db_venta)

    # Recargar con relaciones
    return obtener_venta(db, db_venta.id)


def listar_ventas(
    db: Session,
    estado: str = None,
    cliente_id: int = None,
    fecha_desde: str = None,
    fecha_hasta: str = None,
):
    query = _load_venta_relations(db.query(Venta))

    if estado:
        query = query.filter(Venta.estado == estado)
    if cliente_id:
        query = query.filter(Venta.cliente_id == cliente_id)
    if fecha_desde:
        query = query.filter(Venta.fecha_venta >= fecha_desde)
    if fecha_hasta:
        query = query.filter(Venta.fecha_venta <= fecha_hasta)

    return query.order_by(desc(Venta.fecha_venta)).all()


def obtener_venta(db: Session, venta_id: int):
    return _load_venta_relations(
        db.query(Venta)
    ).filter(Venta.id == venta_id).first()


def actualizar_venta(db: Session, venta_id: int, venta_update: VentaUpdate):
    db_venta = db.query(Venta).filter(Venta.id == venta_id).first()
    if not db_venta:
        return None

    update_data = venta_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_venta, key, value)

    # Recalcular diferencia si cambian los precios
    precio_venta = update_data.get("precio_venta", db_venta.precio_venta)
    precio_toma = update_data.get("precio_toma", db_venta.precio_toma)
    if precio_toma is not None:
        db_venta.diferencia = precio_venta - precio_toma
    else:
        db_venta.diferencia = None

    db_venta.fecha_actualizacion = datetime.utcnow()
    db.commit()
    db.refresh(db_venta)

    return obtener_venta(db, db_venta.id)


def eliminar_venta(db: Session, venta_id: int):
    db_venta = db.query(Venta).filter(Venta.id == venta_id).first()
    if not db_venta:
        return False

    # Revertir estado del auto vendido a Disponible
    if db_venta.auto_vendido_id:
        auto_vendido = db.query(Auto).filter(Auto.id == db_venta.auto_vendido_id).first()
        if auto_vendido:
            estado_disponible = _get_or_create_estado(db, "Disponible")
            auto_vendido.en_stock = True
            auto_vendido.estado_id = estado_disponible.id

    db.delete(db_venta)
    db.commit()
    return True


def obtener_estadisticas_ventas(db: Session):
    """Estadísticas del módulo de ventas."""
    total = db.query(func.count(Venta.id)).scalar() or 0

    # Por estado
    estados = {}
    for est in ["pendiente", "completada", "cancelada"]:
        estados[est] = db.query(func.count(Venta.id)).filter(Venta.estado == est).scalar() or 0

    # Totales monetarios (solo completadas)
    completadas = db.query(Venta).filter(Venta.estado == "completada")

    total_vendido = completadas.with_entities(func.sum(Venta.precio_venta)).scalar() or 0
    total_tomado = completadas.with_entities(
        func.sum(Venta.precio_toma)
    ).filter(Venta.precio_toma.isnot(None)).scalar() or 0
    total_diferencia = completadas.with_entities(
        func.sum(Venta.diferencia)
    ).filter(Venta.diferencia.isnot(None)).scalar() or 0

    # Ventas con toma (parte de pago)
    ventas_con_toma = db.query(func.count(Venta.id)).filter(
        Venta.auto_tomado_id.isnot(None),
        Venta.estado == "completada"
    ).scalar() or 0

    # Ganancia estimada total
    ganancia_total = completadas.with_entities(
        func.sum(Venta.ganancia_estimada)
    ).filter(Venta.ganancia_estimada.isnot(None)).scalar() or 0

    return {
        "total": total,
        "por_estado": estados,
        "total_vendido": total_vendido,
        "total_tomado": total_tomado,
        "total_diferencia": total_diferencia,
        "ventas_con_toma": ventas_con_toma,
        "ganancia_estimada_total": ganancia_total,
    }
