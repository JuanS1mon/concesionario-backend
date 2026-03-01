from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.marca import Marca, MarcaCreate, MarcaUpdate
from app.crud.marca import (
    get_marcas,
    get_marca,
    create_marca,
    update_marca,
    delete_marca
)
from app.api.deps import get_current_admin

router = APIRouter(prefix="/marcas", tags=["marcas"])

@router.get("/", response_model=List[Marca])
def read_marcas(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    try:
        marcas = get_marcas(db, skip=skip, limit=limit)
        return marcas
    except OperationalError as e:
        # Base de datos no disponible
        raise HTTPException(status_code=503, detail=f"DB connection error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{marca_id}", response_model=Marca)
def read_marca(marca_id: int, db: Session = Depends(get_db)):
    try:
        db_marca = get_marca(db, marca_id=marca_id)
    except OperationalError as e:
        raise HTTPException(status_code=503, detail=f"DB connection error: {e}")
    if db_marca is None:
        raise HTTPException(status_code=404, detail="Marca no encontrada")
    return db_marca

@router.post("/", response_model=Marca)
def create_marca_endpoint(
    marca: MarcaCreate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    return create_marca(db, marca)

@router.put("/{marca_id}", response_model=Marca)
def update_marca_endpoint(
    marca_id: int,
    marca: MarcaUpdate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    db_marca = update_marca(db, marca_id=marca_id, marca=marca)
    if db_marca is None:
        raise HTTPException(status_code=404, detail="Marca no encontrada")
    return db_marca

@router.delete("/{marca_id}")
def delete_marca_endpoint(
    marca_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    db_marca = delete_marca(db, marca_id=marca_id)
    if db_marca is None:
        raise HTTPException(status_code=404, detail="Marca no encontrada")
    return {"message": "Marca eliminada exitosamente"}