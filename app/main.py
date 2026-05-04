from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import atletas, checkins, planos_semanais, sessao

app = FastAPI(
    title="GoJohnny API",
    description="Consultoria pessoal de corrida com IA",
    version="1.1.0",
)

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


@app.get("/")
def root():
    return {"app": "GoJohnny API", "status": "online", "version": "1.1.0"}


@app.get("/health")
def health():
    return {"status": "ok"}
