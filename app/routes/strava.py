"""
Strava routes - FASE 1 do plano de integracao.

Rotas internas, todas protegidas por x-api-key, EXCETO /strava/callback
(callback do OAuth do Strava nao tem como receber o header).
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import verify_api_key
from app.core.config import STRAVA_SUCCESS_REDIRECT_URL
from app.schemas.strava import (
    StravaStatusResponse,
    StravaPreferenceUpdate,
    StravaPreferenceResponse,
    StravaLoginResponse,
    StravaActivitiesResponse,
    StravaActivityDetailResponse,
    StravaTodayResponse,
    StravaAnalyzeRequest,
    StravaAnalyzeWeekRequest,
    StravaAnalysisResult,
    StravaDisconnectResponse,
)
from app.services import strava_service


router = APIRouter(prefix="/strava", tags=["strava"])


def _handle_lookup_error(exc: Exception) -> None:
    raise HTTPException(status_code=404, detail=str(exc))


# ---------------------------------------------------------------------------
# 1) STATUS
# ---------------------------------------------------------------------------

@router.get(
    "/status/{apelido}",
    response_model=StravaStatusResponse,
    dependencies=[Depends(verify_api_key)],
)
def status(apelido: str, db: Session = Depends(get_db)):
    try:
        return strava_service.get_strava_status(db, apelido)
    except LookupError as exc:
        _handle_lookup_error(exc)


# ---------------------------------------------------------------------------
# 2) PREFERENCIA
# ---------------------------------------------------------------------------

@router.post(
    "/preferencia/{apelido}",
    response_model=StravaPreferenceResponse,
    dependencies=[Depends(verify_api_key)],
)
def preferencia(
    apelido: str,
    body: StravaPreferenceUpdate,
    db: Session = Depends(get_db),
):
    try:
        return strava_service.set_strava_preference(db, apelido, body.usa_strava)
    except LookupError as exc:
        _handle_lookup_error(exc)


# ---------------------------------------------------------------------------
# 3) LOGIN (gera URL OAuth)
# ---------------------------------------------------------------------------

@router.get(
    "/login/{apelido}",
    response_model=StravaLoginResponse,
    dependencies=[Depends(verify_api_key)],
)
def login(apelido: str, db: Session = Depends(get_db)):
    try:
        return strava_service.build_strava_login_url(db, apelido)
    except LookupError as exc:
        _handle_lookup_error(exc)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# 4) CALLBACK (Strava redireciona aqui apos consentimento)
# ---------------------------------------------------------------------------

@router.get("/callback")
async def callback(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    scope: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    if error:
        return HTMLResponse(
            f"<html><body><h2>Strava: autorizacao recusada</h2><p>{error}</p></body></html>",
            status_code=400,
        )
    if not code or not state:
        raise HTTPException(status_code=400, detail="code e state sao obrigatorios.")

    try:
        result = await strava_service.handle_strava_callback(
            db, code=code, state=state, scope=scope
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    if STRAVA_SUCCESS_REDIRECT_URL:
        return RedirectResponse(url=STRAVA_SUCCESS_REDIRECT_URL, status_code=302)

    return HTMLResponse(
        f"""
        <html>
          <body style="font-family: sans-serif; padding: 24px;">
            <h2>Strava conectado 👊</h2>
            <p>Pode voltar para a conversa com o GoJohnny.</p>
            <p><small>Atleta: {result.get('apelido')}</small></p>
          </body>
        </html>
        """,
        status_code=200,
    )


# ---------------------------------------------------------------------------
# 5) TREINO DE HOJE
# ---------------------------------------------------------------------------

@router.get(
    "/treino-hoje/{apelido}",
    response_model=StravaTodayResponse,
    dependencies=[Depends(verify_api_key)],
)
async def treino_hoje(apelido: str, db: Session = Depends(get_db)):
    try:
        return await strava_service.get_today_run(db, apelido)
    except LookupError as exc:
        _handle_lookup_error(exc)
    except PermissionError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


# ---------------------------------------------------------------------------
# 6) TREINOS DA SEMANA
# ---------------------------------------------------------------------------

@router.get(
    "/treinos-semana/{apelido}",
    response_model=StravaActivitiesResponse,
    dependencies=[Depends(verify_api_key)],
)
async def treinos_semana(
    apelido: str,
    semana_inicio: date = Query(...),
    semana_fim: date = Query(...),
    db: Session = Depends(get_db),
):
    try:
        atividades = await strava_service.get_week_runs(db, apelido, semana_inicio, semana_fim)
    except LookupError as exc:
        _handle_lookup_error(exc)
    except PermissionError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    return {
        "apelido": apelido,
        "total": len(atividades),
        "atividades": atividades,
        "mensagem_usuario": f"{len(atividades)} corridas no Strava nessa janela.",
    }


# ---------------------------------------------------------------------------
# 7) TREINOS RECENTES
# ---------------------------------------------------------------------------

@router.get(
    "/treinos-recentes/{apelido}",
    response_model=StravaActivitiesResponse,
    dependencies=[Depends(verify_api_key)],
)
async def treinos_recentes(
    apelido: str,
    limit: int = Query(10, ge=1, le=30),
    db: Session = Depends(get_db),
):
    try:
        atividades = await strava_service.get_recent_runs(db, apelido, limit=limit)
    except LookupError as exc:
        _handle_lookup_error(exc)
    except PermissionError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    return {
        "apelido": apelido,
        "total": len(atividades),
        "atividades": atividades,
        "mensagem_usuario": f"Ultimas {len(atividades)} corridas no Strava.",
    }


# ---------------------------------------------------------------------------
# 8) ATIVIDADE INDIVIDUAL (detalhe)
# ---------------------------------------------------------------------------

@router.get(
    "/atividade/{apelido}/{activity_id}",
    response_model=StravaActivityDetailResponse,
    dependencies=[Depends(verify_api_key)],
)
async def atividade(apelido: str, activity_id: int, db: Session = Depends(get_db)):
    try:
        result = await strava_service.fetch_activity_detail(db, apelido, activity_id)
    except LookupError as exc:
        _handle_lookup_error(exc)
    except PermissionError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    return {"apelido": apelido, "atividade": result["atividade"], "raw_detail": result["raw_detail"]}


# ---------------------------------------------------------------------------
# 9) ANALISAR TREINO
# ---------------------------------------------------------------------------

@router.post(
    "/analisar-treino/{apelido}",
    response_model=StravaAnalysisResult,
    dependencies=[Depends(verify_api_key)],
)
async def analisar_treino(
    apelido: str,
    body: StravaAnalyzeRequest,
    db: Session = Depends(get_db),
):
    try:
        return await strava_service.analyze_strava_activity_against_plan(
            db,
            apelido,
            body.activity_id,
            salvar_checkin=body.salvar_checkin,
            salvar_memoria_flag=body.salvar_memoria,
        )
    except LookupError as exc:
        _handle_lookup_error(exc)
    except PermissionError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception as exc:
        import logging
        logging.getLogger(__name__).error("analisar-treino falhou: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro interno na analise: {type(exc).__name__}: {exc}")


# ---------------------------------------------------------------------------
# 10) ANALISAR SEMANA
# ---------------------------------------------------------------------------

@router.post(
    "/analisar-semana/{apelido}",
    response_model=StravaAnalysisResult,
    dependencies=[Depends(verify_api_key)],
)
async def analisar_semana(
    apelido: str,
    body: StravaAnalyzeWeekRequest,
    db: Session = Depends(get_db),
):
    try:
        return await strava_service.analyze_strava_week_against_plan(
            db,
            apelido,
            body.semana_inicio,
            body.semana_fim,
            salvar_resumo=body.salvar_resumo,
        )
    except LookupError as exc:
        _handle_lookup_error(exc)
    except PermissionError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception as exc:
        import logging
        logging.getLogger(__name__).error("analisar-semana falhou: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro interno na analise semanal: {type(exc).__name__}: {exc}")


# ---------------------------------------------------------------------------
# 11) TREINOS ÚLTIMOS DIAS
# ---------------------------------------------------------------------------

@router.get(
    "/treinos-ultimos-dias/{apelido}",
    response_model=StravaActivitiesResponse,
    dependencies=[Depends(verify_api_key)],
)
async def treinos_ultimos_dias(
    apelido: str,
    dias: int = Query(10, ge=1, le=90),
    db: Session = Depends(get_db),
):
    try:
        result = await strava_service.get_runs_last_n_days(db, apelido, dias=dias)
    except LookupError as exc:
        _handle_lookup_error(exc)
    except PermissionError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    return {
        "apelido": apelido,
        "total": result["total"],
        "atividades": result["atividades"],
        "mensagem_usuario": result["mensagem_usuario"],
    }


# ---------------------------------------------------------------------------
# 12) DESCONECTAR
# ---------------------------------------------------------------------------

@router.post(
    "/desconectar/{apelido}",
    response_model=StravaDisconnectResponse,
    dependencies=[Depends(verify_api_key)],
)
async def desconectar(apelido: str, db: Session = Depends(get_db)):
    try:
        return await strava_service.disconnect_strava(db, apelido)
    except LookupError as exc:
        _handle_lookup_error(exc)
