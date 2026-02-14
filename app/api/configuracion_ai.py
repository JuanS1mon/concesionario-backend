from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.api.deps import get_current_admin
from app.schemas.configuracion_ai import ConfiguracionAIOut, ConfiguracionAICreate, ConfiguracionAIUpdate
from app.crud.configuracion_ai import (
    get_configuracion_ai,
    create_configuracion_ai,
    update_configuracion_ai,
    delete_configuracion_ai,
)
from app.config import DEEPSEEK_API_KEY

router = APIRouter()


def _mask_key(key: str | None) -> tuple[bool, str | None]:
    if not key:
        return False, None
    return True, key[-4:]


@router.get("/configuracion-ai", response_model=ConfiguracionAIOut)
def read_configuracion_ai(
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    if DEEPSEEK_API_KEY:
        has_key, last4 = _mask_key(DEEPSEEK_API_KEY)
        return ConfiguracionAIOut(
            proveedor="deepseek",
            activo=True,
            has_key=has_key,
            api_key_last4=last4,
            source="env",
        )

    configuracion = get_configuracion_ai(db)
    if not configuracion:
        raise HTTPException(status_code=404, detail="Configuración de IA no encontrada")

    has_key, last4 = _mask_key(configuracion.api_key)
    return ConfiguracionAIOut(
        id=configuracion.id,
        proveedor=configuracion.proveedor,
        activo=configuracion.activo,
        has_key=has_key,
        api_key_last4=last4,
        source="db",
        created_at=configuracion.created_at,
        updated_at=configuracion.updated_at,
    )


@router.post("/configuracion-ai", response_model=ConfiguracionAIOut)
def create_configuracion_ai_endpoint(
    configuracion: ConfiguracionAICreate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    if not configuracion.api_key:
        raise HTTPException(status_code=400, detail="API key requerida")

    db_config = create_configuracion_ai(db, configuracion)
    has_key, last4 = _mask_key(db_config.api_key)
    return ConfiguracionAIOut(
        id=db_config.id,
        proveedor=db_config.proveedor,
        activo=db_config.activo,
        has_key=has_key,
        api_key_last4=last4,
        source="db",
        created_at=db_config.created_at,
        updated_at=db_config.updated_at,
    )


@router.put("/configuracion-ai/{configuracion_id}", response_model=ConfiguracionAIOut)
def update_configuracion_ai_endpoint(
    configuracion_id: int,
    configuracion: ConfiguracionAIUpdate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    db_config = update_configuracion_ai(db, configuracion_id, configuracion)
    if not db_config:
        raise HTTPException(status_code=404, detail="Configuración de IA no encontrada")

    has_key, last4 = _mask_key(db_config.api_key)
    return ConfiguracionAIOut(
        id=db_config.id,
        proveedor=db_config.proveedor,
        activo=db_config.activo,
        has_key=has_key,
        api_key_last4=last4,
        source="db",
        created_at=db_config.created_at,
        updated_at=db_config.updated_at,
    )


@router.delete("/configuracion-ai/{configuracion_id}")
def delete_configuracion_ai_endpoint(
    configuracion_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    db_config = delete_configuracion_ai(db, configuracion_id)
    if not db_config:
        raise HTTPException(status_code=404, detail="Configuración de IA no encontrada")
    return {"message": "Configuración de IA eliminada exitosamente"}
