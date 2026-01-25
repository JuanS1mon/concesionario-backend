from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.modelo import Modelo, ModeloCreate, ModeloUpdate
from app.crud.modelo import (
    get_modelos,
    get_modelo,
    create_modelo,
    update_modelo,
    delete_modelo
)
from app.api.deps import get_current_admin

router = APIRouter(prefix="/modelos", tags=["modelos"])

@router.get("/", response_model=List[Modelo])
def read_modelos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    modelos = get_modelos(db, skip=skip, limit=limit)
    return modelos

@router.get("/{modelo_id}", response_model=Modelo)
def read_modelo(modelo_id: int, db: Session = Depends(get_db)):
    db_modelo = get_modelo(db, modelo_id=modelo_id)
    if db_modelo is None:
        raise HTTPException(status_code=404, detail="Modelo no encontrado")
    return db_modelo

@router.post("/", response_model=Modelo)
def create_modelo_endpoint(
    modelo: ModeloCreate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    return create_modelo(db, modelo)

@router.put("/{modelo_id}", response_model=Modelo)
def update_modelo_endpoint(
    modelo_id: int,
    modelo: ModeloUpdate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    db_modelo = update_modelo(db, modelo_id=modelo_id, modelo=modelo)
    if db_modelo is None:
        raise HTTPException(status_code=404, detail="Modelo no encontrado")
    return db_modelo

@router.delete("/{modelo_id}")
def delete_modelo_endpoint(
    modelo_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    db_modelo = delete_modelo(db, modelo_id=modelo_id)
    if db_modelo is None:
        raise HTTPException(status_code=404, detail="Modelo no encontrado")
    return {"message": "Modelo eliminado exitosamente"}