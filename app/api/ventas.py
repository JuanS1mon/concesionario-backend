from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.api.deps import get_current_admin
from app.schemas.venta import VentaCreate, VentaUpdate, VentaOut
from app.crud.venta import (
    crear_venta,
    listar_ventas,
    obtener_venta,
    actualizar_venta,
    eliminar_venta,
    obtener_estadisticas_ventas,
)
from typing import Optional

router = APIRouter(prefix="/ventas", tags=["ventas"])


@router.post("/", response_model=VentaOut)
def create_venta(
    venta: VentaCreate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    return crear_venta(db, venta)


@router.get("/", response_model=list[VentaOut])
def list_ventas(
    estado: Optional[str] = Query(None),
    cliente_id: Optional[int] = Query(None),
    fecha_desde: Optional[str] = Query(None),
    fecha_hasta: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    return listar_ventas(
        db,
        estado=estado,
        cliente_id=cliente_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )


@router.get("/estadisticas")
def stats_ventas(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    return obtener_estadisticas_ventas(db)


@router.get("/{venta_id}", response_model=VentaOut)
def get_venta(
    venta_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    venta = obtener_venta(db, venta_id)
    if not venta:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    return venta


@router.put("/{venta_id}", response_model=VentaOut)
def update_venta(
    venta_id: int,
    venta_update: VentaUpdate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    venta = actualizar_venta(db, venta_id, venta_update)
    if not venta:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    return venta


@router.delete("/{venta_id}")
def delete_venta(
    venta_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    success = eliminar_venta(db, venta_id)
    if not success:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    return {"message": "Venta eliminada exitosamente"}
