import logging
from typing import Optional
import requests
from sqlalchemy.orm import Session
from app.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL
from app.crud.configuracion_ai import get_configuracion_ai

logger = logging.getLogger(__name__)


class AIConfigError(RuntimeError):
    pass


def get_deepseek_api_key(db: Optional[Session] = None) -> tuple[str | None, str | None]:
    if DEEPSEEK_API_KEY:
        return DEEPSEEK_API_KEY, "env"
    if db is not None:
        db_config = get_configuracion_ai(db)
        if db_config and db_config.api_key:
            return db_config.api_key, "db"
    return None, None


def deepseek_chat(
    messages: list[dict],
    db: Optional[Session] = None,
    temperature: float = 0.2,
    max_tokens: int = 700,
) -> str:
    api_key, _source = get_deepseek_api_key(db)
    if not api_key:
        raise AIConfigError("DeepSeek API key no configurada")

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    response = requests.post(DEEPSEEK_BASE_URL, json=payload, headers=headers, timeout=30)
    if response.status_code >= 400:
        logger.error("DeepSeek error %s: %s", response.status_code, response.text[:500])
        raise AIConfigError("Error al consultar DeepSeek")

    data = response.json()
    choices = data.get("choices") or []
    if not choices:
        raise AIConfigError("Respuesta vacia de DeepSeek")

    message = choices[0].get("message") or {}
    content = message.get("content")
    if not content:
        raise AIConfigError("Respuesta sin contenido de DeepSeek")

    return content
