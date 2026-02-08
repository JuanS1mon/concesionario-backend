from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.cliente import ClienteCreate, ClienteUpdate, ClienteOut
from app.crud.cliente import (
    crear_cliente,
    listar_clientes,
    obtener_cliente,
    actualizar_cliente,
    eliminar_cliente,
    obtener_estadisticas_clientes
)
from typing import Optional

router = APIRouter(prefix="/clientes", tags=["clientes"])


@router.post("/", response_model=ClienteOut)
def create_cliente(cliente: ClienteCreate, db: Session = Depends(get_db)):
    return crear_cliente(db, cliente)


@router.get("/", response_model=list[ClienteOut])
def list_clientes(
    estado: Optional[str] = Query(None),
    calificacion: Optional[str] = Query(None),
    activo: Optional[bool] = Query(None),
    busqueda: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    clientes = listar_clientes(db, estado=estado, calificacion=calificacion, activo=activo, busqueda=busqueda)
    # Agregar conteo de oportunidades
    result = []
    for c in clientes:
        cliente_dict = ClienteOut.model_validate(c)
        cliente_dict.total_oportunidades = len(c.oportunidades) if c.oportunidades else 0
        result.append(cliente_dict)
    return result


@router.get("/estadisticas")
def stats_clientes(db: Session = Depends(get_db)):
    return obtener_estadisticas_clientes(db)


@router.get("/{cliente_id}", response_model=ClienteOut)
def get_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cliente = obtener_cliente(db, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente


@router.put("/{cliente_id}", response_model=ClienteOut)
def update_cliente(cliente_id: int, cliente_update: ClienteUpdate, db: Session = Depends(get_db)):
    cliente = actualizar_cliente(db, cliente_id, cliente_update)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente


@router.delete("/{cliente_id}")
def delete_cliente(cliente_id: int, db: Session = Depends(get_db)):
    success = eliminar_cliente(db, cliente_id)
    if not success:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return {"message": "Cliente eliminado exitosamente"}
