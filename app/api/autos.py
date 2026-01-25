from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.auto import Auto, AutoCreate, AutoUpdate
from app.crud.auto import (
    get_autos,
    get_auto,
    create_auto,
    update_auto,
    delete_auto
)
from app.api.deps import get_current_admin

router = APIRouter(prefix="/autos", tags=["autos"])

@router.get("/", response_model=List[Auto])
def read_autos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    autos = get_autos(db, skip=skip, limit=limit)
    return autos

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