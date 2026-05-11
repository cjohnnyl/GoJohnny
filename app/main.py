import asyncio
import logging

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.request_id import RequestIDMiddleware, request_id_var
from app.routes import atletas, checkins, planos_semanais, sessao, contexto, calendario, oauth, memorias, strava, qa

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)

app = FastAPI(
    title="GoJohnny API",
    description="Consultoria pessoal de corrida com IA",
    version="1.1.0",
)

app.add_middleware(RequestIDMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessao.router)
app.include_router(atletas.router)
app.include_router(checkins.router)
app.include_router(planos_semanais.router)
app.include_router(contexto.router)
app.include_router(calendario.router)
app.include_router(memorias.router)
app.include_router(oauth.router)
app.include_router(strava.router)
app.include_router(qa.router)


@app.exception_handler(asyncio.TimeoutError)
@app.exception_handler(TimeoutError)
async def timeout_handler(request: Request, exc: Exception):
    req_id = request_id_var.get() or "unknown"
    return JSONResponse(
        status_code=503,
        headers={"X-Request-ID": req_id},
        content={
            "error": "timeout",
            "message": "O sistema pode estar acordando agora. Tente novamente em alguns segundos.",
            "request_id": req_id,
            "category": "cold_start_possible",
        },
    )


@app.exception_handler(httpx.TimeoutException)
async def httpx_timeout_handler(request: Request, exc: Exception):
    req_id = request_id_var.get() or "unknown"
    return JSONResponse(
        status_code=503,
        headers={"X-Request-ID": req_id},
        content={
            "error": "upstream_timeout",
            "message": "Serviço externo demorou para responder. Tente novamente em alguns segundos.",
            "request_id": req_id,
            "category": "timeout",
        },
    )


@app.exception_handler(httpx.ConnectError)
async def httpx_connect_error_handler(request: Request, exc: Exception):
    req_id = request_id_var.get() or "unknown"
    return JSONResponse(
        status_code=503,
        headers={"X-Request-ID": req_id},
        content={
            "error": "upstream_unavailable",
            "message": "Não foi possível conectar ao serviço externo. Tente novamente em alguns segundos.",
            "request_id": req_id,
            "category": "timeout",
        },
    )


@app.get("/")
def root():
    return {"app": "GoJohnny API", "status": "online", "version": "1.1.0"}


@app.get("/health")
def health():
    return {"status": "ok"}
