from sqlalchemy.orm import Session
from app.models.auto import Auto
from app.schemas.auto import AutoCreate, AutoUpdate
from typing import Optional

def build_autos_query(
    db: Session,
    marca_id: Optional[int] = None,
    modelo_id: Optional[int] = None,
    anio_min: Optional[int] = None,
    anio_max: Optional[int] = None,
    tipo: Optional[str] = None,
    precio_min: Optional[float] = None,
    precio_max: Optional[float] = None,
    en_stock: Optional[bool] = None,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = "asc"
):
    query = db.query(Auto)

    # Aplicar filtros si existen
    if marca_id is not None:
        query = query.filter(Auto.marca_id == marca_id)

    if modelo_id is not None:
        query = query.filter(Auto.modelo_id == modelo_id)

    if anio_min is not None:
        query = query.filter(Auto.anio >= anio_min)

    if anio_max is not None:
        query = query.filter(Auto.anio <= anio_max)

    if tipo is not None:
        query = query.filter(Auto.tipo == tipo)

    if precio_min is not None:
        query = query.filter(Auto.precio >= precio_min)

    if precio_max is not None:
        query = query.filter(Auto.precio <= precio_max)

    if en_stock is not None:
        query = query.filter(Auto.en_stock == en_stock)

    # Aplicar ordenamiento
    if sort_by == "precio":
        if sort_order == "desc":
            query = query.order_by(Auto.precio.desc())
        else:
            query = query.order_by(Auto.precio.asc())
    elif sort_by == "anio":
        if sort_order == "desc":
            query = query.order_by(Auto.anio.desc())
        else:
            query = query.order_by(Auto.anio.asc())

    return query

def get_autos(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    marca_id: Optional[int] = None,
    modelo_id: Optional[int] = None,
    anio_min: Optional[int] = None,
    anio_max: Optional[int] = None,
    tipo: Optional[str] = None,
    precio_min: Optional[float] = None,
    precio_max: Optional[float] = None,
    en_stock: Optional[bool] = None,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = "asc"
):
    query = build_autos_query(
        db,
        marca_id=marca_id,
        modelo_id=modelo_id,
        anio_min=anio_min,
        anio_max=anio_max,
        tipo=tipo,
        precio_min=precio_min,
        precio_max=precio_max,
        en_stock=en_stock,
        sort_by=sort_by,
        sort_order=sort_order
    )
    return query.offset(skip).limit(limit).all()

def get_autos_count(
    db: Session,
    marca_id: Optional[int] = None,
    modelo_id: Optional[int] = None,
    anio_min: Optional[int] = None,
    anio_max: Optional[int] = None,
    tipo: Optional[str] = None,
    precio_min: Optional[float] = None,
    precio_max: Optional[float] = None,
    en_stock: Optional[bool] = None
):
    query = build_autos_query(
        db,
        marca_id=marca_id,
        modelo_id=modelo_id,
        anio_min=anio_min,
        anio_max=anio_max,
        tipo=tipo,
        precio_min=precio_min,
        precio_max=precio_max,
        en_stock=en_stock
    )
    return query.count()

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