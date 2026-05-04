"""
Centralizacao de leitura/escrita de feature flags por atleta - Fase 1, Bloco 5.

Decisao (com Johnny): flags ficam em colunas BOOLEAN dedicadas na tabela
atletas, com default false. Esse modulo e a UNICA porta autorizada para
ler/escrever as flags - rotas e outros services NAO leem coluna direta
para garantir que regras (como "default seguro" e "audit log") fiquem
sempre aplicadas.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional

from sqlalchemy.orm import Session

from app.models.atleta import Atleta


# Lista canonica de flags conhecidas. Adicionar nova flag aqui + na
# migration + no model. A lista e usada por validacao defensiva.
FLAGS_CONHECIDAS: tuple[str, ...] = (
    "usar_datas_reais",
    "usar_contexto_atleta",
    "usar_google_calendar",
    "usar_strava",
)


@dataclass(frozen=True)
class CapabilitiesAtleta:
    """Snapshot imutavel das flags de um atleta."""
    usar_datas_reais: bool
    usar_contexto_atleta: bool
    usar_google_calendar: bool
    usar_strava: bool

    def to_dict(self) -> dict[str, bool]:
        return {
            "usar_datas_reais": self.usar_datas_reais,
            "usar_contexto_atleta": self.usar_contexto_atleta,
            "usar_google_calendar": self.usar_google_calendar,
            "usar_strava": self.usar_strava,
        }

    def is_enabled(self, flag: str) -> bool:
        if flag not in FLAGS_CONHECIDAS:
            raise ValueError(
                f"Flag desconhecida: {flag!r}. Conhecidas: {FLAGS_CONHECIDAS}"
            )
        return bool(getattr(self, flag))


def capabilities_para(atleta: Atleta) -> CapabilitiesAtleta:
    """Le as flags do model SQLAlchemy de Atleta. Usa default=false
    se a coluna for NULL (caso defensivo - nao deveria acontecer pois
    a migration define NOT NULL DEFAULT false)."""
    return CapabilitiesAtleta(
        usar_datas_reais=bool(getattr(atleta, "usar_datas_reais", False) or False),
        usar_contexto_atleta=bool(getattr(atleta, "usar_contexto_atleta", False) or False),
        usar_google_calendar=bool(getattr(atleta, "usar_google_calendar", False) or False),
        usar_strava=bool(getattr(atleta, "usar_strava", False) or False),
    )


def aplicar_flags(
    db: Session,
    atleta: Atleta,
    *,
    flags: Mapping[str, Optional[bool]],
) -> CapabilitiesAtleta:
    """Atualiza um conjunto de flags do atleta. Apenas chaves conhecidas
    sao aceitas; chaves desconhecidas levantam ValueError. Valor None
    significa 'nao mexer nesta flag'.

    Persiste no banco (commit responsabilidade do caller, ou auto-commit
    se nao houver transacao aberta).
    """
    desconhecidas = set(flags) - set(FLAGS_CONHECIDAS)
    if desconhecidas:
        raise ValueError(
            f"Flags desconhecidas: {sorted(desconhecidas)}. "
            f"Conhecidas: {FLAGS_CONHECIDAS}"
        )

    for nome, valor in flags.items():
        if valor is None:
            continue
        if not isinstance(valor, bool):
            raise TypeError(
                f"Flag {nome!r} deve ser bool, recebido {type(valor).__name__}"
            )
        setattr(atleta, nome, valor)

    db.add(atleta)
    return capabilities_para(atleta)


def defaults_para_novo_usuario() -> dict[str, bool]:
    """Defaults aplicados ao criar um atleta NOVO durante a Fase 1.

    Decisao: novos usuarios entram com flags conservadoras tambem.
    Vamos promover gradualmente conforme cada feature for validada.
    Mudar aqui e seguro pois afeta apenas a criacao de NOVOS atletas
    (usuarios existentes mantem o que tiverem gravado)."""
    return {flag: False for flag in FLAGS_CONHECIDAS}
