from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.estado import Estado, EstadoCreate, EstadoUpdate
from app.crud.estado import (
    get_estados,
    get_estado,
    create_estado,
    update_estado,
    delete_estado
)
from app.api.deps import get_current_admin

router = APIRouter(prefix="/estados", tags=["estados"])

@router.get("/", response_model=List[Estado])
def read_estados(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    estados = get_estados(db, skip=skip, limit=limit)
    return estados

@router.get("/{estado_id}", response_model=Estado)
def read_estado(estado_id: int, db: Session = Depends(get_db)):
    db_estado = get_estado(db, estado_id=estado_id)
    if db_estado is None:
        raise HTTPException(status_code=404, detail="Estado no encontrado")
    return db_estado

@router.post("/", response_model=Estado)
def create_estado_endpoint(
    estado: EstadoCreate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    return create_estado(db, estado)

@router.put("/{estado_id}", response_model=Estado)
def update_estado_endpoint(
    estado_id: int,
    estado: EstadoUpdate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    db_estado = update_estado(db, estado_id=estado_id, estado=estado)
    if db_estado is None:
        raise HTTPException(status_code=404, detail="Estado no encontrado")
    return db_estado

@router.delete("/{estado_id}")
def delete_estado_endpoint(
    estado_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    db_estado = delete_estado(db, estado_id=estado_id)
    if db_estado is None:
        raise HTTPException(status_code=404, detail="Estado no encontrado")
    return {"message": "Estado eliminado exitosamente"}