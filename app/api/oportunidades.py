from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.oportunidad import OportunidadCreate, OportunidadUpdate, OportunidadOut
from app.crud.oportunidad import (
    crear_oportunidad,
    listar_oportunidades,
    obtener_oportunidad,
    actualizar_oportunidad,
    eliminar_oportunidad,
    obtener_estadisticas_oportunidades
)
from typing import Optional

router = APIRouter(prefix="/oportunidades", tags=["oportunidades"])


@router.post("/", response_model=OportunidadOut)
def create_oportunidad(oportunidad: OportunidadCreate, db: Session = Depends(get_db)):
    return crear_oportunidad(db, oportunidad)


@router.get("/", response_model=list[OportunidadOut])
def list_oportunidades(
    etapa: Optional[str] = Query(None),
    prioridad: Optional[str] = Query(None),
    cliente_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    return listar_oportunidades(db, etapa=etapa, prioridad=prioridad, cliente_id=cliente_id)


@router.get("/estadisticas")
def stats_oportunidades(db: Session = Depends(get_db)):
    return obtener_estadisticas_oportunidades(db)


@router.get("/{oportunidad_id}", response_model=OportunidadOut)
def get_oportunidad(oportunidad_id: int, db: Session = Depends(get_db)):
    oportunidad = obtener_oportunidad(db, oportunidad_id)
    if not oportunidad:
        raise HTTPException(status_code=404, detail="Oportunidad no encontrada")
    return oportunidad


@router.put("/{oportunidad_id}", response_model=OportunidadOut)
def update_oportunidad(oportunidad_id: int, oportunidad_update: OportunidadUpdate, db: Session = Depends(get_db)):
    oportunidad = actualizar_oportunidad(db, oportunidad_id, oportunidad_update)
    if not oportunidad:
        raise HTTPException(status_code=404, detail="Oportunidad no encontrada")
    return oportunidad


@router.delete("/{oportunidad_id}")
def delete_oportunidad(oportunidad_id: int, db: Session = Depends(get_db)):
    success = eliminar_oportunidad(db, oportunidad_id)
    if not success:
        raise HTTPException(status_code=404, detail="Oportunidad no encontrada")
    return {"message": "Oportunidad eliminada exitosamente"}
