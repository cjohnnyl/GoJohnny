from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, Any, List
from datetime import date, datetime
from decimal import Decimal
import uuid


def _normalizar_dias(dias: Optional[List[str]]) -> Optional[List[str]]:
    """Normaliza lista de dias para forma canônica (lowercase sem acentos)."""
    if not dias:
        return dias

    # Mapa de normalização (mesmo do plano_service)
    mapa = {
        "segunda": "segunda", "terca": "terca", "quarta": "quarta",
        "quinta": "quinta", "sexta": "sexta", "sabado": "sabado", "domingo": "domingo",
        "terça": "terca", "sábado": "sabado",
        "monday": "segunda", "tuesday": "terca", "wednesday": "quarta",
        "thursday": "quinta", "friday": "sexta", "saturday": "sabado", "sunday": "domingo",
        "seg": "segunda", "ter": "terca", "qua": "quarta", "qui": "quinta",
        "sex": "sexta", "sab": "sabado", "dom": "domingo",
        "mon": "segunda", "tue": "terca", "wed": "quarta", "thu": "quinta",
        "fri": "sexta", "sat": "sabado", "sun": "domingo",
    }

    normalizados = []
    for dia in dias:
        chave = dia.lower().strip() if isinstance(dia, str) else str(dia).lower().strip()
        normalizado = mapa.get(chave, dia)  # fallback ao original se não reconhecer
        normalizados.append(normalizado)
    return normalizados


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

    @field_validator("dias_treino_json", mode="after")
    @classmethod
    def normalizar_dias_entrada(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Normaliza dias_treino_json na entrada para garantir consistência."""
        return _normalizar_dias(v)


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

    @field_validator("dias_treino_json", mode="after")
    @classmethod
    def normalizar_dias_saida(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Normaliza dias_treino_json na saída para garantir consistência."""
        return _normalizar_dias(v)
