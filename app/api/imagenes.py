from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
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
from app.services.cloudinary_service import upload_image_to_cloudinary

router = APIRouter(prefix="/imagenes", tags=["imagenes"])

@router.get("/auto/{auto_id}", response_model=List[ImagenOut])
def read_imagenes_by_auto(auto_id: int, db: Session = Depends(get_db)):
    imagenes = get_imagenes_by_auto(db, auto_id=auto_id)
    return imagenes

@router.post("/upload", response_model=ImagenOut)
def upload_imagen(
    file: UploadFile = File(...),
    auto_id: int = Form(...),
    titulo: str = Form(None),
    descripcion: str = Form(None),
    alt: str = Form(None),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    try:
        result = upload_image_to_cloudinary(file.file, titulo=titulo, descripcion=descripcion, alt=alt)
        imagen_data = ImagenCreate(
            url=result["url"], 
            public_id=result["public_id"], 
            auto_id=auto_id,
            titulo=titulo,
            descripcion=descripcion,
            alt=alt
        )
        return create_imagen(db, imagen_data)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

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