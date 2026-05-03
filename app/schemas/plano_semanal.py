from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Any, List
from datetime import date, datetime
from decimal import Decimal
import uuid


class PlanoSemanalCreate(BaseModel):
    apelido: str
    semana_inicio: date
    objetivo_semana: Optional[str] = None
    volume_planejado_km: Optional[Decimal] = None
    status: Optional[str] = None
    plano: Any
    # Enriquecimento aditivo (Fase 1, Bloco 6) - todos opcionais
    data_inicio: Optional[date] = None
    data_prova: Optional[date] = None
    dias_treino_json: Optional[List[str]] = None
    versao_estrutura: Optional[int] = None
    # Protecao contra sobrescrita (Fase 1, Bloco 9)
    novo_ciclo: bool = Field(
        default=False,
        description=(
            "Se ja existe plano ativo para este atleta, exige true para "
            "criar um novo (que arquivara o anterior). Sem este flag, "
            "o backend retorna 409 Conflict."
        ),
    )


class PlanoSemanalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    atleta_id: uuid.UUID
    semana_inicio: Optional[date] = None
    objetivo_semana: Optional[str] = None
    volume_planejado_km: Optional[Decimal] = None
    status: Optional[str] = None
    plano: Optional[Any] = None
    data_inicio: Optional[date] = None
    data_prova: Optional[date] = None
    dias_treino_json: Optional[List[str]] = None
    versao_estrutura: Optional[int] = None
    criado_em: Optional[datetime] = None
    atualizado_em: Optional[datetime] = None
