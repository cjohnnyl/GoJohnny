"""
Middleware de request_id — gera UUID por request, expõe via context var e header X-Request-ID.

Nunca loga: x-api-key, Authorization, access_token, refresh_token, cookies.
"""

import logging
import time
import uuid
from contextvars import ContextVar
from re import sub

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("gojohnny.request")

# Compartilhado entre middleware e handlers de exceção do mesmo request
request_id_var: ContextVar[str] = ContextVar("request_id", default="")

_APELIDO_PATTERN_SEGMENTS = {
    "atletas", "strava", "planos-semanais", "checkins",
    "contexto", "memorias", "calendario", "oauth", "qa",
}


def _extract_apelido(path: str) -> str:
    """Extrai apelido de paths como /atletas/{apelido}, /strava/status/{apelido}."""
    parts = [p for p in path.split("/") if p]
    for i, part in enumerate(parts):
        if part in _APELIDO_PATTERN_SEGMENTS and i + 1 < len(parts):
            candidate = parts[i + 1]
            # Pular sub-rotas conhecidas (status, treino-hoje, etc.)
            if not candidate.startswith("qa") and not any(
                c in candidate for c in ["-", ".", "callback", "login", "cleanup"]
            ):
                return candidate
            # Para qa/cleanup/{apelido}
            if part == "qa" and i + 1 < len(parts) and parts[i + 1] == "cleanup" and i + 2 < len(parts):
                return parts[i + 2]
    return ""


def _categorize_status(status_code: int) -> str:
    if status_code == 401:
        return "auth_error"
    if status_code == 422:
        return "validation_error"
    if status_code == 404:
        return "not_found"
    if status_code == 409:
        return "strava_not_connected"
    if status_code == 503:
        return "cold_start_possible"
    if status_code >= 500:
        return "internal_error"
    return "ok"


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        req_id = str(uuid.uuid4())
        request_id_var.set(req_id)
        start = time.time()

        response = await call_next(request)

        duration_ms = int((time.time() - start) * 1000)
        apelido = _extract_apelido(request.url.path)
        category = _categorize_status(response.status_code)

        response.headers["X-Request-ID"] = req_id

        log_extra = {
            "request_id": req_id,
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": duration_ms,
            "category": category,
        }
        if apelido:
            log_extra["apelido"] = apelido

        level = logging.WARNING if response.status_code >= 400 else logging.INFO
        logger.log(
            level,
            "%s %s %s %dms [%s] rid=%s",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            category,
            req_id,
        )

        return response
