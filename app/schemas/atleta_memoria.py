from typing import Optional, List, Any
from datetime import datetime, date
from pydantic import BaseModel, Field


class AtletaMemoriaCreate(BaseModel):
    tipo: str = Field(..., description="Tipo de memória: perfil, objetivo, preferencia, treino_realizado, feedback, etc.")
    chave: str = Field(..., description="Identificador único da memória")
    valor_texto: Optional[str] = Field(None, description="Valor textual")
    valor_json: Optional[dict[str, Any]] = Field(None, description="Valor JSON estruturado")
    origem: str = Field(..., description="Origem: conversa, importacao_chat_antigo, sistema")
    importancia: int = Field(3, ge=1, le=5, description="Importância: 1-5, sendo 5 crítico")
    confianca: float = Field(1.0, ge=0, le=1, description="Confiança: 0-1")
    semana_inicio: Optional[date] = Field(None, description="Semana inicial se aplicável")


class AtletaMemoriaUpdate(BaseModel):
    valor_texto: Optional[str] = None
    valor_json: Optional[dict[str, Any]] = None
    importancia: Optional[int] = Field(None, ge=1, le=5)
    confianca: Optional[float] = Field(None, ge=0, le=1)
    ativo: Optional[bool] = None


class AtletaMemoriaRead(BaseModel):
    id: str
    atleta_id: str
    tipo: str
    chave: str
    valor_texto: Optional[str]
    valor_json: Optional[dict[str, Any]]
    origem: str
    importancia: int
    confianca: float
    semana_inicio: Optional[date]
    ativo: bool
    criado_em: datetime
    atualizado_em: datetime

    model_config = {"from_attributes": True}


class ResumoSemanalCreate(BaseModel):
    semana_inicio: date = Field(..., description="Data de início da semana")
    resumo: str = Field(..., description="Resumo da semana")
    aderencia: str = Field("normal", description="Aderencia: parcial, normal, excelente")
    pontos_positivos: List[str] = Field(default_factory=list)
    pontos_atencao: List[str] = Field(default_factory=list)
    decisoes_treinador: List[str] = Field(default_factory=list)
    proximo_foco: Optional[str] = None


class ResumoSemanalRead(BaseModel):
    id: str
    atleta_id: str
    semana_inicio: date
    resumo: str
    aderencia: str
    pontos_positivos: List[str]
    pontos_atencao: List[str]
    decisoes_treinador: List[str]
    proximo_foco: Optional[str]
    criado_em: datetime

    model_config = {"from_attributes": True}


class MemoriasResumoResponse(BaseModel):
    apelido: str
    memorias: List[AtletaMemoriaRead]


class BuscaMemorias(BaseModel):
    resultados: List[AtletaMemoriaRead]
    total: int
