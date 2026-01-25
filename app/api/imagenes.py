from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.imagen import ImagenOut, ImagenCreate
from app.crud.imagen import (
    get_imagenes_by_auto,
    create_imagen,
    delete_imagen
)
from app.api.deps import get_current_admin

router = APIRouter(prefix="/imagenes", tags=["imagenes"])

@router.get("/auto/{auto_id}", response_model=List[ImagenOut])
def read_imagenes_by_auto(auto_id: int, db: Session = Depends(get_db)):
    imagenes = get_imagenes_by_auto(db, auto_id=auto_id)
    return imagenes

@router.post("/", response_model=ImagenOut)
def create_imagen_endpoint(
    imagen: ImagenCreate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    return create_imagen(db, imagen)

@router.delete("/{imagen_id}")
def delete_imagen_endpoint(
    imagen_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    db_imagen = delete_imagen(db, imagen_id=imagen_id)
    if db_imagen is None:
        raise HTTPException(status_code=404, detail="Imagen no encontrada")
    return {"message": "Imagen eliminada exitosamente"}