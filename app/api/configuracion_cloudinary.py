from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.configuracion_cloudinary import ConfiguracionCloudinary, ConfiguracionCloudinaryCreate, ConfiguracionCloudinaryUpdate
from app.crud.configuracion_cloudinary import (
    get_configuracion_cloudinary,
    create_configuracion_cloudinary,
    update_configuracion_cloudinary,
    delete_configuracion_cloudinary
)
from app.api.deps import get_current_admin

router = APIRouter()

@router.get("/configuracion-cloudinary", response_model=ConfiguracionCloudinary)
def read_configuracion_cloudinary(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    configuracion = get_configuracion_cloudinary(db)
    if not configuracion:
        raise HTTPException(status_code=404, detail="Configuración de Cloudinary no encontrada")
    return configuracion

@router.post("/configuracion-cloudinary", response_model=ConfiguracionCloudinary)
def create_configuracion_cloudinary_endpoint(
    configuracion: ConfiguracionCloudinaryCreate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    return create_configuracion_cloudinary(db, configuracion)

@router.put("/configuracion-cloudinary/{configuracion_id}", response_model=ConfiguracionCloudinary)
def update_configuracion_cloudinary_endpoint(
    configuracion_id: int,
    configuracion: ConfiguracionCloudinaryUpdate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    db_configuracion = update_configuracion_cloudinary(db, configuracion_id, configuracion)
    if not db_configuracion:
        raise HTTPException(status_code=404, detail="Configuración de Cloudinary no encontrada")
    return db_configuracion

@router.delete("/configuracion-cloudinary/{configuracion_id}")
def delete_configuracion_cloudinary_endpoint(
    configuracion_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    db_configuracion = delete_configuracion_cloudinary(db, configuracion_id)
    if not db_configuracion:
        raise HTTPException(status_code=404, detail="Configuración de Cloudinary no encontrada")
    return {"message": "Configuración eliminada exitosamente"}