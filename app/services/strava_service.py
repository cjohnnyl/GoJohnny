"""
Strava Service - FASE 1 do plano de integracao.

Princpios:
- Strava e fonte de evidencia, nunca de decisao.
- Nunca consultar Strava automaticamente. Sempre exigir consentimento.
- Tokens armazenados criptografados (Fernet) usando STRAVA_TOKEN_ENCRYPTION_KEY.
- Tokens nunca aparecem em logs ou respostas publicas.
- Plano nunca e alterado automaticamente. Analises sao sugestoes.
"""

from __future__ import annotations

import base64
import hashlib
import json
import time
import uuid
from datetime import datetime, date, timedelta, timezone, time as dtime
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode

import httpx
from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.config import (
    STRAVA_CLIENT_ID,
    STRAVA_CLIENT_SECRET,
    STRAVA_REDIRECT_URI,
    STRAVA_SCOPES,
    STRAVA_TOKEN_ENCRYPTION_KEY,
)
from app.models.atleta import Atleta
from app.models.plano_semanal import PlanoSemanal
from app.models.strava import (
    StravaPreference,
    StravaConnection,
    StravaActivityCache,
    StravaTrainingAnalysis,
    StravaSyncLog,
)
from app.services.memoria_service import (
    salvar_memoria,
    salvar_resumo_semanal,
    get_atleta_by_apelido,
)
from app.schemas.atleta_memoria import AtletaMemoriaCreate, ResumoSemanalCreate


# ============================================================================
# Endpoints Strava
# ============================================================================

STRAVA_AUTH_URL = "https://www.strava.com/oauth/authorize"
STRAVA_TOKEN_URL = "https://www.strava.com/oauth/token"
STRAVA_DEAUTH_URL = "https://www.strava.com/oauth/deauthorize"
STRAVA_API_BASE = "https://www.strava.com/api/v3"


# ============================================================================
# Helpers gerais
# ============================================================================

def _agora_utc() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_apelido(apelido: str) -> str:
    return (apelido or "").strip().lower()


def _formatar_pace(sec_km: Optional[int]) -> Optional[str]:
    if not sec_km or sec_km <= 0:
        return None
    minutos = sec_km // 60
    segundos = sec_km % 60
    return f"{minutos}:{segundos:02d}/km"


def _calcular_pace_sec_km(distance_m: Optional[float], moving_time_s: Optional[int]) -> Optional[int]:
    if not distance_m or not moving_time_s or distance_m <= 0:
        return None
    km = distance_m / 1000.0
    if km <= 0:
        return None
    return int(round(moving_time_s / km))


def _parse_dt(value: Any) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except Exception:
            return None
    return None


# ============================================================================
# Criptografia de tokens (Fernet)
# ============================================================================

def _derive_fernet_key(raw: str) -> bytes:
    """
    Aceita STRAVA_TOKEN_ENCRYPTION_KEY como:
    - chave Fernet ja gerada (urlsafe base64 32 bytes), OU
    - string arbitraria que sera derivada via SHA-256 + base64 urlsafe.
    """
    if not raw:
        raise RuntimeError("STRAVA_TOKEN_ENCRYPTION_KEY nao configurado.")

    # Se ja for chave Fernet valida, usar direto
    try:
        Fernet(raw.encode())
        return raw.encode()
    except Exception:
        pass

    digest = hashlib.sha256(raw.encode()).digest()
    return base64.urlsafe_b64encode(digest)


def _get_fernet() -> Fernet:
    return Fernet(_derive_fernet_key(STRAVA_TOKEN_ENCRYPTION_KEY))


def _encrypt_token(token: str) -> str:
    if not token:
        raise ValueError("Token vazio nao pode ser criptografado.")
    return _get_fernet().encrypt(token.encode()).decode()


def _decrypt_token(token_encrypted: str) -> str:
    try:
        return _get_fernet().decrypt(token_encrypted.encode()).decode()
    except InvalidToken as exc:
        raise RuntimeError("Falha ao descriptografar token Strava (chave invalida ou dado corrompido).") from exc


# ============================================================================
# Logging interno (auditoria)
# ============================================================================

def _log_sync(
    db: Session,
    *,
    atleta_id: Optional[uuid.UUID],
    endpoint: str,
    metodo: str = "GET",
    status_code: Optional[int] = None,
    sucesso: bool = False,
    erro_texto: Optional[str] = None,
    rate_limit_limit: Optional[str] = None,
    rate_limit_usage: Optional[str] = None,
    read_rate_limit_limit: Optional[str] = None,
    read_rate_limit_usage: Optional[str] = None,
    request_params_json: Optional[Dict[str, Any]] = None,
    response_resumo_json: Optional[Dict[str, Any]] = None,
) -> None:
    try:
        log = StravaSyncLog(
            atleta_id=atleta_id,
            endpoint=endpoint,
            metodo=metodo,
            status_code=status_code,
            sucesso=sucesso,
            erro_texto=erro_texto,
            rate_limit_limit=rate_limit_limit,
            rate_limit_usage=rate_limit_usage,
            read_rate_limit_limit=read_rate_limit_limit,
            read_rate_limit_usage=read_rate_limit_usage,
            request_params_json=request_params_json,
            response_resumo_json=response_resumo_json,
        )
        db.add(log)
        db.commit()
    except Exception:
        db.rollback()


# ============================================================================
# Helpers de atleta / preferencia / conexao
# ============================================================================

def _obter_atleta(db: Session, apelido: str) -> Atleta:
    atleta = get_atleta_by_apelido(db, apelido)
    if not atleta:
        raise LookupError(f"Atleta '{apelido}' nao encontrado.")
    return atleta


def _obter_preferencia(db: Session, atleta_id: uuid.UUID) -> Optional[StravaPreference]:
    return (
        db.query(StravaPreference)
        .filter(StravaPreference.atleta_id == atleta_id)
        .first()
    )


def _obter_conexao(db: Session, atleta_id: uuid.UUID) -> Optional[StravaConnection]:
    return (
        db.query(StravaConnection)
        .filter(StravaConnection.atleta_id == atleta_id)
        .first()
    )


# ============================================================================
# 1) get_strava_status
# ============================================================================

def get_strava_status(db: Session, apelido: str) -> Dict[str, Any]:
    atleta = _obter_atleta(db, apelido)
    pref = _obter_preferencia(db, atleta.id)
    conn = _obter_conexao(db, atleta.id)

    usa_strava = pref.usa_strava if pref else None
    perguntar = pref.perguntar_strava if pref else True
    conectado = bool(conn)
    active = bool(conn and conn.active)

    if usa_strava is None:
        mensagem = "Nao perguntei ainda se voce usa Strava. Quando relatar treino, eu pergunto."
    elif usa_strava is False:
        mensagem = "Voce me disse que nao usa Strava. Sigo na analise manual."
    elif not conectado:
        mensagem = "Voce usa Strava mas ainda nao conectou. Me avisa quando quiser que eu te passo o link."
    elif not active:
        mensagem = "Sua conexao com Strava esta inativa. Vamos reconectar quando quiser."
    else:
        mensagem = "Strava conectado. Me autoriza na conversa antes de eu consultar."

    precisa_conectar = bool(usa_strava is True and not active)

    return {
        "apelido": atleta.apelido,
        "usa_strava": usa_strava,
        "perguntar_strava": perguntar,
        "conectado": conectado,
        "active": active,
        "scopes": conn.scope if conn else None,
        "last_sync_at": conn.last_sync_at if conn else None,
        "expires_at_ts": conn.expires_at_ts if conn else None,
        "precisa_conectar": precisa_conectar,
        "mensagem_usuario": mensagem,
    }


# ============================================================================
# 2) set_strava_preference
# ============================================================================

def set_strava_preference(
    db: Session,
    apelido: str,
    usa_strava: bool,
    *,
    salvar_memoria_pref: bool = True,
) -> Dict[str, Any]:
    atleta = _obter_atleta(db, apelido)

    pref = _obter_preferencia(db, atleta.id)
    if pref:
        pref.usa_strava = usa_strava
        pref.ultima_resposta_usuario = "sim" if usa_strava else "nao"
        # Se disse que nao usa, nao insistir
        if usa_strava is False:
            pref.perguntar_strava = False
    else:
        pref = StravaPreference(
            atleta_id=atleta.id,
            usa_strava=usa_strava,
            perguntar_strava=False if usa_strava is False else True,
            ultima_resposta_usuario="sim" if usa_strava else "nao",
            origem="conversa",
        )
        db.add(pref)

    db.commit()

    if salvar_memoria_pref:
        try:
            valor = "Atleta usa Strava" if usa_strava else "Atleta nao usa Strava"
            salvar_memoria(
                db,
                str(atleta.id),
                AtletaMemoriaCreate(
                    tipo="preferencia",
                    chave="usa_strava",
                    valor_texto=valor,
                    origem="conversa",
                    importancia=3,
                    confianca=1.0,
                ),
            )
        except Exception:
            db.rollback()

    if usa_strava:
        mensagem = "Anotado: voce usa Strava. Quando quiser conectar, eu te passo o link."
    else:
        mensagem = "Anotado: voce nao usa Strava. Vou seguir na analise manual e nao insistir."

    return {
        "apelido": atleta.apelido,
        "usa_strava": usa_strava,
        "perguntar_strava": pref.perguntar_strava,
        "salvo": True,
        "mensagem_usuario": mensagem,
    }


# ============================================================================
# 3) build_strava_login_url
# ============================================================================

def _build_state(atleta_apelido: str) -> str:
    """
    State opaco com timestamp e apelido. Em base64 urlsafe.
    Validado em handle_strava_callback.
    """
    payload = {
        "apelido": atleta_apelido,
        "ts": int(time.time()),
        "nonce": uuid.uuid4().hex[:12],
    }
    raw = json.dumps(payload, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).decode()


def _parse_state(state: str) -> Optional[Dict[str, Any]]:
    try:
        raw = base64.urlsafe_b64decode(state.encode())
        payload = json.loads(raw.decode())
        if not isinstance(payload, dict) or "apelido" not in payload:
            return None
        # state expira em 30 minutos
        ts = int(payload.get("ts", 0))
        if time.time() - ts > 1800:
            return None
        return payload
    except Exception:
        return None


def build_strava_login_url(db: Session, apelido: str) -> Dict[str, Any]:
    atleta = _obter_atleta(db, apelido)

    if not STRAVA_CLIENT_ID or not STRAVA_REDIRECT_URI:
        raise RuntimeError("STRAVA_CLIENT_ID ou STRAVA_REDIRECT_URI nao configurados.")

    state = _build_state(atleta.apelido)
    scopes = STRAVA_SCOPES or "read,activity:read"

    params = {
        "client_id": STRAVA_CLIENT_ID,
        "redirect_uri": STRAVA_REDIRECT_URI,
        "response_type": "code",
        "approval_prompt": "auto",
        "scope": scopes,
        "state": state,
    }
    url = f"{STRAVA_AUTH_URL}?{urlencode(params)}"

    # Marcar oferta_conexao_exibida=true
    pref = _obter_preferencia(db, atleta.id)
    if pref:
        pref.oferta_conexao_exibida = True
        db.commit()

    return {
        "redirect_url": url,
        "scopes": scopes,
        "mensagem_usuario": "Abre esse link e autoriza o GoJohnny no Strava. Depois volta aqui que eu confirmo a conexao.",
    }


# ============================================================================
# 4) handle_strava_callback
# ============================================================================

async def handle_strava_callback(
    db: Session,
    *,
    code: str,
    state: str,
    scope: Optional[str] = None,
) -> Dict[str, Any]:
    if not STRAVA_CLIENT_ID or not STRAVA_CLIENT_SECRET or not STRAVA_REDIRECT_URI:
        raise RuntimeError("Credenciais Strava nao configuradas.")

    state_payload = _parse_state(state)
    if not state_payload:
        raise ValueError("State invalido ou expirado.")

    apelido = state_payload["apelido"]
    atleta = _obter_atleta(db, apelido)

    payload = {
        "client_id": STRAVA_CLIENT_ID,
        "client_secret": STRAVA_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(STRAVA_TOKEN_URL, data=payload)
    except Exception as exc:
        _log_sync(
            db,
            atleta_id=atleta.id,
            endpoint="oauth/token",
            metodo="POST",
            sucesso=False,
            erro_texto=f"erro de rede: {type(exc).__name__}",
        )
        raise RuntimeError("Falha de rede ao trocar code com Strava.") from exc

    if resp.status_code != 200:
        _log_sync(
            db,
            atleta_id=atleta.id,
            endpoint="oauth/token",
            metodo="POST",
            status_code=resp.status_code,
            sucesso=False,
            erro_texto="status nao 200",
        )
        raise RuntimeError("Strava retornou erro ao trocar code por tokens.")

    data = resp.json()
    access_token = data.get("access_token")
    refresh_token = data.get("refresh_token")
    expires_at = int(data.get("expires_at", 0))
    token_type = data.get("token_type", "Bearer")
    athlete = data.get("athlete") or {}
    strava_athlete_id = int(athlete.get("id", 0)) if athlete.get("id") else 0

    if not access_token or not refresh_token or not strava_athlete_id:
        raise RuntimeError("Resposta Strava sem tokens ou athlete id.")

    # Criptografa tokens
    access_enc = _encrypt_token(access_token)
    refresh_enc = _encrypt_token(refresh_token)
    expires_at_ts = datetime.fromtimestamp(expires_at, tz=timezone.utc) if expires_at else None

    conn = _obter_conexao(db, atleta.id)
    if conn:
        conn.strava_athlete_id = strava_athlete_id
        conn.access_token_encrypted = access_enc
        conn.refresh_token_encrypted = refresh_enc
        conn.expires_at = expires_at
        conn.expires_at_ts = expires_at_ts
        conn.token_type = token_type
        conn.scope = scope or conn.scope
        conn.active = True
        conn.revoked_at = None
        conn.last_refresh_at = _agora_utc()
        conn.raw_athlete_json = athlete
    else:
        conn = StravaConnection(
            atleta_id=atleta.id,
            strava_athlete_id=strava_athlete_id,
            access_token_encrypted=access_enc,
            refresh_token_encrypted=refresh_enc,
            expires_at=expires_at,
            expires_at_ts=expires_at_ts,
            token_type=token_type,
            scope=scope,
            active=True,
            raw_athlete_json=athlete,
        )
        db.add(conn)

    # Atualiza preferencia para usa_strava=True
    pref = _obter_preferencia(db, atleta.id)
    if pref:
        pref.usa_strava = True
    else:
        pref = StravaPreference(atleta_id=atleta.id, usa_strava=True, perguntar_strava=True, origem="oauth")
        db.add(pref)

    db.commit()

    _log_sync(
        db,
        atleta_id=atleta.id,
        endpoint="oauth/token",
        metodo="POST",
        status_code=200,
        sucesso=True,
        response_resumo_json={"strava_athlete_id": strava_athlete_id},
    )

    return {
        "apelido": atleta.apelido,
        "conectado": True,
        "scope": scope,
    }


# ============================================================================
# 5) refresh_access_token_if_needed
# ============================================================================

async def refresh_access_token_if_needed(
    db: Session,
    atleta_id: uuid.UUID,
    *,
    margin_seconds: int = 120,
) -> Optional[StravaConnection]:
    conn = _obter_conexao(db, atleta_id)
    if not conn or not conn.active:
        return None

    now_ts = int(time.time())
    if conn.expires_at and conn.expires_at - now_ts > margin_seconds:
        return conn

    try:
        refresh_token = _decrypt_token(conn.refresh_token_encrypted)
    except Exception:
        # Tokens corrompidos: marcar inativa
        conn.active = False
        conn.revoked_at = _agora_utc()
        db.commit()
        return None

    payload = {
        "client_id": STRAVA_CLIENT_ID,
        "client_secret": STRAVA_CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(STRAVA_TOKEN_URL, data=payload)
    except Exception as exc:
        _log_sync(
            db,
            atleta_id=atleta_id,
            endpoint="oauth/token (refresh)",
            metodo="POST",
            sucesso=False,
            erro_texto=f"erro de rede: {type(exc).__name__}",
        )
        return None

    if resp.status_code == 401:
        # Revogado pelo usuario
        conn.active = False
        conn.revoked_at = _agora_utc()
        db.commit()
        _log_sync(
            db,
            atleta_id=atleta_id,
            endpoint="oauth/token (refresh)",
            metodo="POST",
            status_code=401,
            sucesso=False,
            erro_texto="token revogado",
        )
        return None

    if resp.status_code != 200:
        _log_sync(
            db,
            atleta_id=atleta_id,
            endpoint="oauth/token (refresh)",
            metodo="POST",
            status_code=resp.status_code,
            sucesso=False,
        )
        return None

    data = resp.json()
    new_access = data.get("access_token")
    new_refresh = data.get("refresh_token")
    new_expires_at = int(data.get("expires_at", 0))

    if not new_access or not new_refresh:
        return None

    conn.access_token_encrypted = _encrypt_token(new_access)
    conn.refresh_token_encrypted = _encrypt_token(new_refresh)
    conn.expires_at = new_expires_at
    conn.expires_at_ts = datetime.fromtimestamp(new_expires_at, tz=timezone.utc)
    conn.last_refresh_at = _agora_utc()
    db.commit()

    return conn


async def _get_valid_access_token(db: Session, atleta_id: uuid.UUID) -> Optional[str]:
    conn = await refresh_access_token_if_needed(db, atleta_id)
    if not conn or not conn.active:
        return None
    try:
        return _decrypt_token(conn.access_token_encrypted)
    except Exception:
        return None


# ============================================================================
# Cliente HTTP Strava generico
# ============================================================================

async def _strava_get(
    db: Session,
    atleta: Atleta,
    path: str,
    params: Optional[Dict[str, Any]] = None,
) -> Tuple[int, Any, Dict[str, str]]:
    access_token = await _get_valid_access_token(db, atleta.id)
    if not access_token:
        raise PermissionError("Sem token Strava valido. Reconectar.")

    url = f"{STRAVA_API_BASE}{path}"
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(url, headers=headers, params=params or {})
    except Exception as exc:
        _log_sync(
            db,
            atleta_id=atleta.id,
            endpoint=path,
            metodo="GET",
            sucesso=False,
            erro_texto=f"erro de rede: {type(exc).__name__}",
            request_params_json=params,
        )
        raise

    rl = resp.headers.get("X-RateLimit-Limit")
    ru = resp.headers.get("X-RateLimit-Usage")
    rrl = resp.headers.get("X-Readratelimit-Limit")
    rru = resp.headers.get("X-Readratelimit-Usage")

    body: Any = None
    try:
        body = resp.json()
    except Exception:
        body = None

    if resp.status_code == 401:
        # Marca inativa
        conn = _obter_conexao(db, atleta.id)
        if conn:
            conn.active = False
            conn.revoked_at = _agora_utc()
            db.commit()

    sucesso = 200 <= resp.status_code < 300
    _log_sync(
        db,
        atleta_id=atleta.id,
        endpoint=path,
        metodo="GET",
        status_code=resp.status_code,
        sucesso=sucesso,
        rate_limit_limit=rl,
        rate_limit_usage=ru,
        read_rate_limit_limit=rrl,
        read_rate_limit_usage=rru,
        request_params_json=params,
        erro_texto=None if sucesso else (str(body)[:300] if body else None),
    )

    return resp.status_code, body, dict(resp.headers)


# ============================================================================
# Normalizacao + cache
# ============================================================================

def _normalizar_atividade(raw: Dict[str, Any]) -> Dict[str, Any]:
    distance_m = raw.get("distance")
    moving = raw.get("moving_time")
    pace_sec = _calcular_pace_sec_km(distance_m, moving)

    duracao_min = None
    if moving:
        duracao_min = round(moving / 60.0, 1)

    return {
        "strava_activity_id": int(raw.get("id")) if raw.get("id") else None,
        "name": raw.get("name"),
        "sport_type": raw.get("sport_type"),
        "type": raw.get("type"),
        "start_date": _parse_dt(raw.get("start_date")),
        "start_date_local": _parse_dt(raw.get("start_date_local")),
        "timezone": raw.get("timezone"),
        "distance_m": float(distance_m) if distance_m is not None else None,
        "distance_km": round(distance_m / 1000.0, 2) if distance_m else None,
        "moving_time_s": moving,
        "elapsed_time_s": raw.get("elapsed_time"),
        "duracao_min": duracao_min,
        "total_elevation_gain_m": raw.get("total_elevation_gain"),
        "average_speed_mps": raw.get("average_speed"),
        "max_speed_mps": raw.get("max_speed"),
        "average_pace_sec_km": pace_sec,
        "average_pace_text": _formatar_pace(pace_sec),
        "average_heartrate": raw.get("average_heartrate"),
        "max_heartrate": raw.get("max_heartrate"),
        "average_cadence": raw.get("average_cadence"),
        "average_watts": raw.get("average_watts"),
        "weighted_average_watts": raw.get("weighted_average_watts"),
        "kilojoules": raw.get("kilojoules"),
        "calories": raw.get("calories"),
        "suffer_score": raw.get("suffer_score"),
        "has_heartrate": raw.get("has_heartrate"),
        "elev_high": raw.get("elev_high"),
        "elev_low": raw.get("elev_low"),
        "private": raw.get("private"),
        "visibility": raw.get("visibility"),
    }


def _upsert_activity_cache(
    db: Session,
    atleta_id: uuid.UUID,
    raw: Dict[str, Any],
    *,
    is_detail: bool = False,
) -> StravaActivityCache:
    norm = _normalizar_atividade(raw)
    activity_id = norm["strava_activity_id"]

    cache = (
        db.query(StravaActivityCache)
        .filter(
            and_(
                StravaActivityCache.atleta_id == atleta_id,
                StravaActivityCache.strava_activity_id == activity_id,
            )
        )
        .first()
    )

    now = _agora_utc()
    if not cache:
        cache = StravaActivityCache(
            atleta_id=atleta_id,
            strava_activity_id=activity_id,
        )
        db.add(cache)

    cache.name = norm["name"]
    cache.sport_type = norm["sport_type"]
    cache.type = norm["type"]
    cache.start_date = norm["start_date"]
    cache.start_date_local = norm["start_date_local"]
    cache.timezone = norm["timezone"]
    cache.distance_m = norm["distance_m"]
    cache.moving_time_s = norm["moving_time_s"]
    cache.elapsed_time_s = norm["elapsed_time_s"]
    cache.total_elevation_gain_m = norm["total_elevation_gain_m"]
    cache.average_speed_mps = norm["average_speed_mps"]
    cache.max_speed_mps = norm["max_speed_mps"]
    cache.average_pace_sec_km = norm["average_pace_sec_km"]
    cache.average_pace_text = norm["average_pace_text"]
    cache.average_heartrate = norm["average_heartrate"]
    cache.max_heartrate = norm["max_heartrate"]
    cache.average_cadence = norm["average_cadence"]
    cache.average_watts = norm["average_watts"]
    cache.weighted_average_watts = norm["weighted_average_watts"]
    cache.kilojoules = norm["kilojoules"]
    cache.calories = norm["calories"]
    cache.suffer_score = norm["suffer_score"]
    cache.has_heartrate = norm["has_heartrate"]
    cache.elev_high = norm["elev_high"]
    cache.elev_low = norm["elev_low"]
    cache.private = norm["private"]
    cache.visibility = norm["visibility"]

    if is_detail:
        cache.raw_detail_json = raw
        cache.synced_detail_at = now
    else:
        cache.raw_summary_json = raw
        cache.synced_summary_at = now

    db.commit()
    db.refresh(cache)
    return cache


def _activity_cache_to_summary(cache: StravaActivityCache) -> Dict[str, Any]:
    return {
        "strava_activity_id": cache.strava_activity_id,
        "name": cache.name,
        "sport_type": cache.sport_type,
        "type": cache.type,
        "start_date_local": cache.start_date_local,
        "timezone": cache.timezone,
        "distance_km": float(cache.distance_m) / 1000.0 if cache.distance_m is not None else None,
        "moving_time_s": cache.moving_time_s,
        "elapsed_time_s": cache.elapsed_time_s,
        "duracao_min": round(cache.moving_time_s / 60.0, 1) if cache.moving_time_s else None,
        "total_elevation_gain_m": float(cache.total_elevation_gain_m) if cache.total_elevation_gain_m is not None else None,
        "average_pace_text": cache.average_pace_text,
        "average_pace_sec_km": cache.average_pace_sec_km,
        "average_speed_mps": float(cache.average_speed_mps) if cache.average_speed_mps is not None else None,
        "average_heartrate": float(cache.average_heartrate) if cache.average_heartrate is not None else None,
        "max_heartrate": float(cache.max_heartrate) if cache.max_heartrate is not None else None,
        "has_heartrate": cache.has_heartrate,
        "suffer_score": cache.suffer_score,
        "private": cache.private,
    }


def _is_run(sport_type: Optional[str], type_field: Optional[str]) -> bool:
    candidates = {"Run", "TrailRun", "VirtualRun"}
    if sport_type and sport_type in candidates:
        return True
    if type_field and type_field in candidates:
        return True
    return False


# ============================================================================
# 6) fetch_athlete_activities
# ============================================================================

async def fetch_athlete_activities(
    db: Session,
    apelido: str,
    *,
    after: Optional[int] = None,
    before: Optional[int] = None,
    per_page: int = 30,
    page: int = 1,
    only_runs: bool = True,
) -> List[Dict[str, Any]]:
    atleta = _obter_atleta(db, apelido)
    params: Dict[str, Any] = {"per_page": per_page, "page": page}
    if after:
        params["after"] = after
    if before:
        params["before"] = before

    status_code, body, _ = await _strava_get(db, atleta, "/athlete/activities", params=params)

    if status_code == 429:
        raise RuntimeError("Strava rate limit (429). Tente em alguns minutos.")
    if status_code == 401:
        raise PermissionError("Conexao Strava invalida ou revogada.")
    if status_code != 200 or not isinstance(body, list):
        raise RuntimeError(f"Strava retornou erro: status {status_code}.")

    resultado: List[Dict[str, Any]] = []
    conn = _obter_conexao(db, atleta.id)
    if conn:
        conn.last_sync_at = _agora_utc()
        db.commit()

    for raw in body:
        if only_runs and not _is_run(raw.get("sport_type"), raw.get("type")):
            continue
        cache = _upsert_activity_cache(db, atleta.id, raw, is_detail=False)
        resultado.append(_activity_cache_to_summary(cache))

    return resultado


# ============================================================================
# 7) fetch_activity_detail
# ============================================================================

async def fetch_activity_detail(
    db: Session,
    apelido: str,
    activity_id: int,
) -> Dict[str, Any]:
    atleta = _obter_atleta(db, apelido)
    status_code, body, _ = await _strava_get(db, atleta, f"/activities/{activity_id}")

    if status_code == 429:
        raise RuntimeError("Strava rate limit (429). Tente em alguns minutos.")
    if status_code == 401:
        raise PermissionError("Conexao Strava invalida ou revogada.")
    if status_code == 404:
        raise LookupError(f"Atividade {activity_id} nao encontrada no Strava.")
    if status_code != 200 or not isinstance(body, dict):
        raise RuntimeError(f"Strava retornou erro: status {status_code}.")

    cache = _upsert_activity_cache(db, atleta.id, body, is_detail=True)
    summary = _activity_cache_to_summary(cache)

    return {
        "atividade": summary,
        "raw_detail": body,
    }


# ============================================================================
# 8) fetch_activity_streams (placeholder)
# ============================================================================

async def fetch_activity_streams(
    db: Session,
    apelido: str,
    activity_id: int,
    *,
    keys: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Fase avancada. Implementacao basica: busca, mas nao cacheia automaticamente."""
    atleta = _obter_atleta(db, apelido)
    keys_param = ",".join(keys or ["time", "distance", "heartrate", "velocity_smooth"])
    params = {"keys": keys_param, "key_by_type": "true"}
    status_code, body, _ = await _strava_get(
        db, atleta, f"/activities/{activity_id}/streams", params=params
    )
    if status_code != 200:
        raise RuntimeError(f"Strava streams retornou status {status_code}.")
    return body or {}


# ============================================================================
# 9) get_today_run
# ============================================================================

def _epoch_for_date(d: date, *, end: bool = False) -> int:
    t = dtime(23, 59, 59) if end else dtime(0, 0, 0)
    dt = datetime.combine(d, t, tzinfo=timezone.utc)
    return int(dt.timestamp())


async def get_today_run(db: Session, apelido: str) -> Dict[str, Any]:
    today = _agora_utc().date()
    after = _epoch_for_date(today - timedelta(days=1), end=False)
    before = _epoch_for_date(today, end=True)

    atividades = await fetch_athlete_activities(
        db, apelido, after=after, before=before, per_page=30, page=1, only_runs=True
    )

    # filtra somente as do dia local de hoje (UTC) - Strava ja retorna da janela
    atividades_hoje = []
    for a in atividades:
        sd = a.get("start_date_local")
        if sd and sd.date() == today:
            atividades_hoje.append(a)

    if not atividades_hoje:
        return {
            "apelido": apelido,
            "encontrou": False,
            "mensagem_usuario": "Nao encontrei corrida no Strava para hoje.",
        }

    if len(atividades_hoje) > 1:
        return {
            "apelido": apelido,
            "encontrou": True,
            "multiplas": True,
            "atividades": atividades_hoje,
            "mensagem_usuario": f"Encontrei {len(atividades_hoje)} corridas hoje. Qual quer analisar?",
        }

    return {
        "apelido": apelido,
        "encontrou": True,
        "multiplas": False,
        "atividade": atividades_hoje[0],
        "mensagem_usuario": "Encontrei tua corrida de hoje no Strava.",
    }


# ============================================================================
# 10) get_week_runs
# ============================================================================

async def get_week_runs(
    db: Session,
    apelido: str,
    semana_inicio: date,
    semana_fim: date,
) -> List[Dict[str, Any]]:
    after = _epoch_for_date(semana_inicio, end=False)
    before = _epoch_for_date(semana_fim, end=True)

    atividades = await fetch_athlete_activities(
        db, apelido, after=after, before=before, per_page=50, page=1, only_runs=True
    )
    return atividades


# ============================================================================
# 11) get_recent_runs
# ============================================================================

async def get_recent_runs(
    db: Session,
    apelido: str,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    coletadas: List[Dict[str, Any]] = []
    page = 1
    per_page = 30
    max_pages = 6  # limite de seguranca

    while len(coletadas) < limit and page <= max_pages:
        lote = await fetch_athlete_activities(
            db, apelido, per_page=per_page, page=page, only_runs=True
        )
        if not lote:
            break
        coletadas.extend(lote)
        page += 1

    coletadas.sort(key=lambda a: a.get("start_date_local") or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    return coletadas[:limit]


# ============================================================================
# 12) analyze_strava_activity_against_plan
# ============================================================================

DIA_SEMANA_PT = {
    0: "segunda",
    1: "terca",
    2: "quarta",
    3: "quinta",
    4: "sexta",
    5: "sabado",
    6: "domingo",
}


def _plano_ativo(db: Session, atleta_id: uuid.UUID) -> Optional[PlanoSemanal]:
    return (
        db.query(PlanoSemanal)
        .filter(
            and_(
                PlanoSemanal.atleta_id == atleta_id,
                PlanoSemanal.status.in_(["ativo", "vigente", "atual"]),
            )
        )
        .order_by(PlanoSemanal.semana_inicio.desc())
        .first()
    )


def _treino_planejado_para_dia(plano: Optional[PlanoSemanal], dt: datetime) -> Optional[Dict[str, Any]]:
    if not plano or not plano.plano:
        return None
    plan_data = plano.plano if isinstance(plano.plano, dict) else {}
    treinos = plan_data.get("treinos") or []
    dia_pt = DIA_SEMANA_PT.get(dt.weekday())
    for t in treinos:
        if (t.get("dia") or "").strip().lower() == dia_pt:
            return t
    return None


def _parse_pace_range(pace: Optional[str]) -> Optional[Tuple[int, int]]:
    """ '6:20-5:50/km' -> (segundos_min, segundos_max) onde min=mais lento, max=mais rapido """
    if not pace:
        return None
    s = pace.replace("/km", "").strip()
    try:
        if "-" in s:
            a, b = s.split("-", 1)
            sec_a = _pace_text_to_sec(a)
            sec_b = _pace_text_to_sec(b)
            if sec_a is None or sec_b is None:
                return None
            return (max(sec_a, sec_b), min(sec_a, sec_b))
        sec = _pace_text_to_sec(s)
        if sec is None:
            return None
        return (sec, sec)
    except Exception:
        return None


def _pace_text_to_sec(text: str) -> Optional[int]:
    try:
        parts = text.strip().split(":")
        if len(parts) != 2:
            return None
        return int(parts[0]) * 60 + int(parts[1])
    except Exception:
        return None


def _parse_km_range(km_text: Optional[str]) -> Optional[Tuple[float, float]]:
    if not km_text:
        return None
    s = str(km_text).strip()
    try:
        if "-" in s:
            a, b = s.split("-", 1)
            return (float(a), float(b))
        v = float(s)
        return (v, v)
    except Exception:
        return None


def _gerar_analise_treino(
    planejado: Optional[Dict[str, Any]],
    executado: Dict[str, Any],
) -> Dict[str, Any]:
    pontos_positivos: List[str] = []
    pontos_atencao: List[str] = []
    aderencia = "parcial"
    plano_deve_mudar = False
    tipo_acao = "manter"
    decisao = ""

    exec_pace = executado.get("average_pace_sec_km")
    exec_km = executado.get("distance_km")
    exec_duracao = executado.get("duracao_min")

    comparativo: Dict[str, Any] = {
        "pace": {"planejado": (planejado or {}).get("pace") if planejado else None, "executado": executado.get("average_pace_text")},
        "duracao_min": {"planejado": (planejado or {}).get("duracao_min") if planejado else None, "executado": exec_duracao},
        "distancia_km": {"planejado": (planejado or {}).get("estimativa_km") if planejado else None, "executado": exec_km},
        "tipo_planejado": (planejado or {}).get("tipo") if planejado else None,
    }

    if not planejado:
        decisao = "Sem treino planejado para esse dia. Registrei a execucao como evidencia."
        aderencia = "parcial"
        return {
            "comparativo": comparativo,
            "aderencia": aderencia,
            "pontos_positivos": pontos_positivos,
            "pontos_atencao": pontos_atencao,
            "decisao_treinador": decisao,
            "plano_deve_mudar": plano_deve_mudar,
            "tipo_acao_recomendada": tipo_acao,
        }

    # Pace
    pace_range = _parse_pace_range(planejado.get("pace"))
    pace_dentro = None
    if pace_range and exec_pace:
        slow, fast = pace_range  # slow > fast em segundos (mais lento = numero maior)
        pace_dentro = fast <= exec_pace <= slow
        if pace_dentro:
            pontos_positivos.append(f"Pace dentro da faixa planejada ({planejado.get('pace')}).")
        else:
            if exec_pace < fast:
                pontos_atencao.append(
                    f"Pace mais rapido que o planejado ({executado.get('average_pace_text')} vs {planejado.get('pace')})."
                )
            else:
                pontos_atencao.append(
                    f"Pace mais lento que o planejado ({executado.get('average_pace_text')} vs {planejado.get('pace')})."
                )

    # Distancia
    km_range = _parse_km_range(planejado.get("estimativa_km"))
    if km_range and exec_km is not None:
        lo, hi = km_range
        margem = max(0.5, (hi - lo) * 0.5)
        if lo - margem <= exec_km <= hi + margem:
            pontos_positivos.append(f"Distancia coerente com o plano ({exec_km:.2f} km).")
        elif exec_km < lo - margem:
            pontos_atencao.append(f"Distancia abaixo do planejado ({exec_km:.2f} km vs {planejado.get('estimativa_km')} km).")
        else:
            pontos_atencao.append(f"Distancia acima do planejado ({exec_km:.2f} km vs {planejado.get('estimativa_km')} km).")

    # Duracao
    plan_dur = planejado.get("duracao_min")
    if plan_dur and exec_duracao:
        delta_pct = abs(exec_duracao - plan_dur) / plan_dur
        if delta_pct <= 0.20:
            pontos_positivos.append(f"Duracao dentro do esperado ({exec_duracao:.0f} min).")
        else:
            pontos_atencao.append(f"Duracao fora do esperado ({exec_duracao:.0f} min vs {plan_dur} min).")

    # Heuristica de regenerativo
    tipo = (planejado.get("tipo") or "").lower()
    if "regenerativo" in tipo and pace_dentro is False and exec_pace and pace_range:
        slow, fast = pace_range
        if exec_pace < fast:
            pontos_atencao.append("Regenerativo virou moderado: aceleracao acima do alvo.")

    # Aderencia geral
    n_pos = len(pontos_positivos)
    n_aten = len(pontos_atencao)
    if n_aten == 0 and n_pos >= 2:
        aderencia = "boa"
        decisao = "Treino feito dentro do plano. Manda o proximo igual."
        tipo_acao = "manter"
    elif n_aten == 0:
        aderencia = "boa"
        decisao = "Execucao alinhada com o plano."
        tipo_acao = "manter"
    elif n_aten <= 1 and n_pos >= 1:
        aderencia = "parcial"
        decisao = "Treino feito, mas com desvio. Registrei pra calibrar."
        tipo_acao = "manter"
    else:
        aderencia = "baixa"
        decisao = "Execucao com varios desvios. Sem reagir agora; se virar padrao, ajustamos."
        tipo_acao = "manter"

    return {
        "comparativo": comparativo,
        "aderencia": aderencia,
        "pontos_positivos": pontos_positivos,
        "pontos_atencao": pontos_atencao,
        "decisao_treinador": decisao,
        "plano_deve_mudar": plano_deve_mudar,
        "tipo_acao_recomendada": tipo_acao,
    }


async def analyze_strava_activity_against_plan(
    db: Session,
    apelido: str,
    activity_id: int,
    *,
    salvar_checkin: bool = False,
    salvar_memoria_flag: bool = False,
) -> Dict[str, Any]:
    atleta = _obter_atleta(db, apelido)

    detalhe = await fetch_activity_detail(db, apelido, activity_id)
    executado = detalhe["atividade"]

    plano = _plano_ativo(db, atleta.id)

    sd_local = executado.get("start_date_local")
    if isinstance(sd_local, datetime):
        ref_dt = sd_local
    else:
        ref_dt = _agora_utc()

    planejado = _treino_planejado_para_dia(plano, ref_dt)

    analise = _gerar_analise_treino(planejado, executado)

    memoria_sugerida: Optional[Dict[str, Any]] = None
    checkin_sugerido: Optional[Dict[str, Any]] = None

    # Sugestao de memoria
    if analise["aderencia"] == "boa":
        memoria_sugerida = {
            "tipo": "treino_realizado",
            "chave": f"strava_{activity_id}",
            "valor_texto": f"Treino {executado.get('name')} executado dentro do plano em {ref_dt.date().isoformat()}.",
            "importancia": 3,
        }
    elif analise["pontos_atencao"]:
        memoria_sugerida = {
            "tipo": "feedback_treino",
            "chave": f"strava_{activity_id}",
            "valor_texto": "; ".join(analise["pontos_atencao"]),
            "importancia": 4,
        }

    # Sugestao de check-in
    checkin_sugerido = {
        "data": ref_dt.date().isoformat(),
        "tipo": (planejado or {}).get("tipo") if planejado else executado.get("sport_type"),
        "distancia_km": executado.get("distance_km"),
        "duracao_min": executado.get("duracao_min"),
        "pace": executado.get("average_pace_text"),
        "fonte": "strava",
        "strava_activity_id": activity_id,
    }

    salvo = {"memoria": False, "checkin": False, "resumo_semanal": False}

    if salvar_memoria_flag and memoria_sugerida:
        try:
            salvar_memoria(
                db,
                str(atleta.id),
                AtletaMemoriaCreate(
                    tipo=memoria_sugerida["tipo"],
                    chave=memoria_sugerida["chave"],
                    valor_texto=memoria_sugerida.get("valor_texto"),
                    valor_json={"strava_activity_id": activity_id, "analise": analise},
                    origem="conversa",
                    importancia=memoria_sugerida.get("importancia", 3),
                    confianca=1.0,
                ),
            )
            salvo["memoria"] = True
        except Exception:
            db.rollback()

    # Persistir analise
    analysis = StravaTrainingAnalysis(
        atleta_id=atleta.id,
        plano_id=plano.id if plano else None,
        strava_activity_id=activity_id,
        periodo="treino",
        data_inicio=ref_dt.date(),
        data_fim=ref_dt.date(),
        titulo=executado.get("name"),
        treino_planejado_json=planejado,
        treino_executado_json=_executado_to_jsonable(executado),
        comparativo_json=analise["comparativo"],
        aderencia=analise["aderencia"],
        pontos_positivos=analise["pontos_positivos"],
        pontos_atencao=analise["pontos_atencao"],
        decisao_treinador=analise["decisao_treinador"],
        plano_deve_mudar=analise["plano_deve_mudar"],
        tipo_acao_recomendada=analise["tipo_acao_recomendada"],
        memoria_criada=salvo["memoria"],
        checkin_criado=salvo["checkin"],
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    return {
        "periodo": "treino",
        "titulo": executado.get("name"),
        "planejado": planejado,
        "executado": _executado_to_jsonable(executado),
        "comparativo": analise["comparativo"],
        "aderencia": analise["aderencia"],
        "pontos_positivos": analise["pontos_positivos"],
        "pontos_atencao": analise["pontos_atencao"],
        "decisao_treinador": analise["decisao_treinador"],
        "plano_deve_mudar": analise["plano_deve_mudar"],
        "tipo_acao_recomendada": analise["tipo_acao_recomendada"],
        "memoria_sugerida": memoria_sugerida,
        "checkin_sugerido": checkin_sugerido,
        "resumo_semanal_sugerido": None,
        "salvo": salvo,
        "analise_id": str(analysis.id),
    }


def _executado_to_jsonable(executado: Dict[str, Any]) -> Dict[str, Any]:
    """Converte datetime/numerics para tipos JSON-friendly."""
    out: Dict[str, Any] = {}
    for k, v in executado.items():
        if isinstance(v, datetime):
            out[k] = v.isoformat()
        else:
            out[k] = v
    return out


# ============================================================================
# 13) analyze_strava_week_against_plan
# ============================================================================

async def analyze_strava_week_against_plan(
    db: Session,
    apelido: str,
    semana_inicio: date,
    semana_fim: date,
    *,
    salvar_resumo: bool = False,
) -> Dict[str, Any]:
    atleta = _obter_atleta(db, apelido)

    plano = (
        db.query(PlanoSemanal)
        .filter(
            and_(
                PlanoSemanal.atleta_id == atleta.id,
                PlanoSemanal.semana_inicio == semana_inicio,
            )
        )
        .first()
    )
    if not plano:
        plano = _plano_ativo(db, atleta.id)

    atividades = await get_week_runs(db, apelido, semana_inicio, semana_fim)

    treinos_plan = []
    if plano and plano.plano and isinstance(plano.plano, dict):
        treinos_plan = plano.plano.get("treinos") or []

    n_planejados = len(treinos_plan)
    n_executados = len(atividades)

    pontos_positivos: List[str] = []
    pontos_atencao: List[str] = []

    if n_planejados > 0:
        if n_executados >= n_planejados:
            pontos_positivos.append(f"Aderencia: {n_executados}/{n_planejados} treinos executados.")
        elif n_executados >= n_planejados * 0.6:
            pontos_atencao.append(f"Aderencia parcial: {n_executados}/{n_planejados} treinos.")
        else:
            pontos_atencao.append(f"Aderencia baixa: {n_executados}/{n_planejados} treinos.")
    else:
        pontos_positivos.append(f"{n_executados} corridas no Strava nessa janela.")

    volume_total_km = sum((a.get("distance_km") or 0) for a in atividades)
    volume_planejado_km = float(plano.volume_planejado_km) if plano and plano.volume_planejado_km else None

    if volume_planejado_km:
        if volume_total_km >= volume_planejado_km * 0.9:
            pontos_positivos.append(f"Volume {volume_total_km:.1f} km coerente com plano de {volume_planejado_km:.1f} km.")
        elif volume_total_km < volume_planejado_km * 0.6:
            pontos_atencao.append(f"Volume {volume_total_km:.1f} km bem abaixo do planejado ({volume_planejado_km:.1f} km).")

    if n_planejados > 0 and n_executados >= n_planejados and not pontos_atencao:
        aderencia = "boa"
    elif pontos_atencao and not pontos_positivos:
        aderencia = "baixa"
    else:
        aderencia = "parcial"

    decisao = {
        "boa": "Semana redonda. Pode evoluir um pouco na proxima.",
        "parcial": "Semana cumprida em parte. Mantemos o desenho.",
        "baixa": "Semana com aderencia baixa. Vamos ajustar a proxima a realidade do atleta.",
    }.get(aderencia, "Semana registrada. Sem mudanca automatica no plano.")

    comparativo = {
        "treinos_planejados": n_planejados,
        "treinos_executados": n_executados,
        "volume_total_km": round(volume_total_km, 2),
        "volume_planejado_km": volume_planejado_km,
    }

    resumo_sugerido = {
        "semana_inicio": semana_inicio.isoformat(),
        "resumo": (
            f"Semana de {semana_inicio.isoformat()} a {semana_fim.isoformat()}: "
            f"{n_executados} corridas, {volume_total_km:.1f} km. "
            f"Aderencia: {aderencia}."
        ),
        "aderencia": aderencia,
        "pontos_positivos": pontos_positivos,
        "pontos_atencao": pontos_atencao,
        "decisoes_treinador": [decisao],
        "proximo_foco": None,
    }

    salvo = {"memoria": False, "checkin": False, "resumo_semanal": False}

    if salvar_resumo:
        try:
            salvar_resumo_semanal(
                db,
                str(atleta.id),
                ResumoSemanalCreate(**resumo_sugerido),
            )
            salvo["resumo_semanal"] = True
        except Exception:
            db.rollback()

    analysis = StravaTrainingAnalysis(
        atleta_id=atleta.id,
        plano_id=plano.id if plano else None,
        strava_activity_id=None,
        periodo="semana",
        data_inicio=semana_inicio,
        data_fim=semana_fim,
        titulo=f"Semana {semana_inicio.isoformat()}",
        treino_planejado_json={"treinos": treinos_plan, "volume_planejado_km": volume_planejado_km},
        treino_executado_json={"atividades": [_executado_to_jsonable(a) for a in atividades]},
        comparativo_json=comparativo,
        aderencia=aderencia,
        pontos_positivos=pontos_positivos,
        pontos_atencao=pontos_atencao,
        decisao_treinador=decisao,
        plano_deve_mudar=False,
        tipo_acao_recomendada="manter",
        resumo_semanal_criado=salvo["resumo_semanal"],
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    return {
        "periodo": "semana",
        "titulo": f"Semana {semana_inicio.isoformat()}",
        "planejado": {"treinos": treinos_plan, "volume_planejado_km": volume_planejado_km},
        "executado": {"atividades": [_executado_to_jsonable(a) for a in atividades]},
        "comparativo": comparativo,
        "aderencia": aderencia,
        "pontos_positivos": pontos_positivos,
        "pontos_atencao": pontos_atencao,
        "decisao_treinador": decisao,
        "plano_deve_mudar": False,
        "tipo_acao_recomendada": "manter",
        "memoria_sugerida": None,
        "checkin_sugerido": None,
        "resumo_semanal_sugerido": resumo_sugerido,
        "salvo": salvo,
        "analise_id": str(analysis.id),
    }


# ============================================================================
# Disconnect
# ============================================================================

async def disconnect_strava(db: Session, apelido: str) -> Dict[str, Any]:
    atleta = _obter_atleta(db, apelido)
    conn = _obter_conexao(db, atleta.id)
    if not conn:
        return {
            "desconectado": False,
            "mensagem_usuario": "Voce nao tem conexao Strava ativa.",
        }

    # Tenta deauthorize na Strava (best-effort)
    try:
        access_token = await _get_valid_access_token(db, atleta.id)
        if access_token:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(
                    STRAVA_DEAUTH_URL,
                    headers={"Authorization": f"Bearer {access_token}"},
                )
    except Exception:
        pass

    db.delete(conn)
    db.commit()

    return {
        "desconectado": True,
        "mensagem_usuario": "Strava desconectado. Quando quiser reconectar, e so avisar.",
    }
