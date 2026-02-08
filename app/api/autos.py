from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.schemas.auto import Auto, AutoCreate, AutoUpdate, AutoList
from app.crud.auto import (
    get_autos,
    get_autos_count,
    get_auto,
    create_auto,
    update_auto,
    delete_auto
)
from app.api.deps import get_current_admin

router = APIRouter(prefix="/autos", tags=["autos"])

@router.get("/", response_model=List[Auto])
def read_autos(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    marca_id: Optional[int] = Query(None),
    modelo_id: Optional[int] = Query(None),
    anio_min: Optional[int] = Query(None),
    anio_max: Optional[int] = Query(None),
    tipo: Optional[str] = Query(None),
    precio_min: Optional[float] = Query(None),
    precio_max: Optional[float] = Query(None),
    en_stock: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    # Usar anio_min y anio_max en lugar de anio
    autos = get_autos(
        db,
        skip=skip,
        limit=limit,
        marca_id=marca_id,
        modelo_id=modelo_id,
        anio_min=anio_min,
        anio_max=anio_max,
        tipo=tipo,
        precio_min=precio_min,
        precio_max=precio_max,
        en_stock=en_stock
    )
    return autos

@router.get("/paginated", response_model=AutoList)
def read_autos_paginated(
    skip: int = Query(0, ge=0),
    limit: int = Query(12, ge=1, le=1000),
    marca_id: Optional[int] = Query(None),
    modelo_id: Optional[int] = Query(None),
    anio_min: Optional[int] = Query(None),
    anio_max: Optional[int] = Query(None),
    tipo: Optional[str] = Query(None),
    precio_min: Optional[float] = Query(None),
    precio_max: Optional[float] = Query(None),
    en_stock: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    autos = get_autos(
        db,
        skip=skip,
        limit=limit,
        marca_id=marca_id,
        modelo_id=modelo_id,
        anio_min=anio_min,
        anio_max=anio_max,
        tipo=tipo,
        precio_min=precio_min,
        precio_max=precio_max,
        en_stock=en_stock
    )
    total = get_autos_count(
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
    return {
        "items": autos,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.get("/{auto_id}", response_model=Auto)
def read_auto(auto_id: int, db: Session = Depends(get_db)):
    db_auto = get_auto(db, auto_id=auto_id)
    if db_auto is None:
        raise HTTPException(status_code=404, detail="Auto no encontrado")
    return db_auto

@router.post("/", response_model=Auto)
def create_auto_endpoint(
    auto: AutoCreate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    return create_auto(db, auto)

@router.put("/{auto_id}", response_model=Auto)
def update_auto_endpoint(
    auto_id: int,
    auto: AutoUpdate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    db_auto = update_auto(db, auto_id=auto_id, auto=auto)
    if db_auto is None:
        raise HTTPException(status_code=404, detail="Auto no encontrado")
    return db_auto

@router.delete("/{auto_id}")
def delete_auto_endpoint(
    auto_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    db_auto = delete_auto(db, auto_id=auto_id)
    if db_auto is None:
        raise HTTPException(status_code=404, detail="Auto no encontrado")
    return {"message": "Auto eliminado exitosamente"}