"""
Servico de plano semanal - Fase 1, Blocos 6, 8 e 9.

Concentra:
  - regra de protecao contra sobrescrita (Bloco 9)
  - aplicacao de defaults aditivos do Fase 1
  - logging estruturado de toda criacao/atualizacao
  - validacao basica antes de gravar
  - enriquecimento de plano com datas reais (Fase 2, Etapa 1)

Regra de protecao (decidida com Johnny):
  Se ja existe plano com status='ativo' para o atleta, a criacao de um
  NOVO plano so e permitida com novo_ciclo=True. Sem essa flag, o
  servico levanta SobrescritaProtegida (a route mapeia para HTTP 409).
  Quando novo_ciclo=True, o plano anterior e marcado como 'arquivado'
  na MESMA transacao do novo plano. Nada e apagado.

Enriquecimento de datas (Fase 2, Etapa 1):
  Se a flag usar_datas_reais estiver ativa E houver data_inicio, data_prova
  e dias_treino_json, o servico enriquece cada treino do plano com a data
  correspondente em formato ISO 8601 ("2026-05-06").
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any, Optional, Dict

from sqlalchemy.orm import Session

from app.models.atleta import Atleta
from app.models.plano_semanal import PlanoSemanal
from app.schemas.atleta_memoria import AtletaMemoriaCreate
from app.schemas.plano_semanal import PlanoSemanalCreate
from app.services.calendar_engine import (
    gerar_calendario,
    normalizar_dia_da_semana,
    nome_canonico_do_weekday,
)


logger = logging.getLogger("gojohnny.plano_service")


STATUS_ATIVO = "ativo"
STATUS_SUBSTITUIDO = "substituido"


# Mapa de normalização: aceita português (com/sem acento), inglês (maiúscula/minúscula)
# Sempre retorna formato interno: "segunda", "terca", "quarta", "quinta", "sexta", "sabado", "domingo"
_MAPA_NORMALIZACAO_DIAS: dict[str, str] = {
    # português (sem acento - forma canônica)
    "segunda": "segunda",
    "terca": "terca",
    "quarta": "quarta",
    "quinta": "quinta",
    "sexta": "sexta",
    "sabado": "sabado",
    "domingo": "domingo",

    # português (com acento)
    "terça": "terca",
    "sábado": "sabado",

    # inglês (lowercase)
    "monday": "segunda",
    "tuesday": "terca",
    "wednesday": "quarta",
    "thursday": "quinta",
    "friday": "sexta",
    "saturday": "sabado",
    "sunday": "domingo",

    # abreviações em português
    "seg": "segunda",
    "ter": "terca",
    "qua": "quarta",
    "qui": "quinta",
    "sex": "sexta",
    "sab": "sabado",
    "dom": "domingo",

    # abreviações em inglês
    "mon": "segunda",
    "tue": "terca",
    "wed": "quarta",
    "thu": "quinta",
    "fri": "sexta",
    "sat": "sabado",
    "sun": "domingo",
}


def _normalizar_dia(dia: str) -> Optional[str]:
    """Normaliza qualquer variante de dia da semana para forma canônica.

    Aceita:
      - português com acento: "terça", "sábado"
      - português sem acento: "terca", "sabado"
      - português abreviado: "ter", "sab"
      - inglês maiúscula/minúscula: "Tuesday", "tuesday"
      - inglês abreviado: "tue", "Tue"

    Retorna sempre lowercase sem acento: "terca", "sabado", etc.
    Retorna None se não reconhecer.
    """
    if not isinstance(dia, str):
        return None

    chave = dia.lower().strip()
    return _MAPA_NORMALIZACAO_DIAS.get(chave)


class SobrescritaProtegida(Exception):
    """Levantada quando ha tentativa de criar plano sem novo_ciclo
    enquanto o atleta ainda tem plano ativo."""

    def __init__(self, plano_atual_id: str, semana_inicio: str):
        self.plano_atual_id = plano_atual_id
        self.semana_inicio = semana_inicio
        super().__init__(
            f"Atleta ja tem plano ativo (id={plano_atual_id}, "
            f"semana_inicio={semana_inicio}). Para criar um novo, "
            f"envie novo_ciclo=true. Sem isso, o backend protege o "
            f"plano existente contra sobrescrita."
        )


def _plano_ativo_de(db: Session, atleta_id) -> Optional[PlanoSemanal]:
    return (
        db.query(PlanoSemanal)
        .filter(
            PlanoSemanal.atleta_id == atleta_id,
            PlanoSemanal.status == STATUS_ATIVO,
        )
        .order_by(PlanoSemanal.semana_inicio.desc())
        .first()
    )


def _detectar_versao_estrutura(data: PlanoSemanalCreate) -> int:
    """Decide versao_estrutura quando o caller nao informa.
    Versao 2 se o plano traz datas reais; senao versao 1 (legado)."""
    if data.versao_estrutura is not None:
        return int(data.versao_estrutura)
    if data.data_inicio is not None or data.data_prova is not None:
        return 2
    if data.dias_treino_json:
        return 2
    return 1


def _mapear_treinos_com_datas(
    plano_jsonb: dict,
    data_inicio: date,
    data_prova: date,
    dias_treino: list[str]
) -> dict:
    """Enriquece treinos do plano_jsonb com datas reais do calendario.

    Lê cada treino em plano_jsonb['treinos'] e adiciona 'data' em ISO 8601.
    Mapeia na ordem: 1º treino de "terça" pega 1ª terça do calendário, etc.

    Se um treino não tiver dia_semana ou o dia não existir no calendário,
    deixa sem data (treino recebe data=None).

    Retorna uma cópia enriquecida de plano_jsonb.
    """
    logger.info(
        "plano.mapear_treinos_iniciado data_inicio=%s data_prova=%s dias_treino=%s",
        data_inicio, data_prova, dias_treino
    )

    # 0.5. Normalizar dias_treino para forma canônica ANTES de CalendarEngine
    dias_treino_normalizados = []
    for dia in dias_treino:
        dia_normalizado = _normalizar_dia(dia)
        if dia_normalizado is None:
            logger.warning(
                "plano.dia_nao_reconhecido_em_entrada dia=%s (pulando)",
                dia
            )
            continue
        dias_treino_normalizados.append(dia_normalizado)

    if not dias_treino_normalizados:
        logger.error(
            "plano.nenhum_dia_valido_apos_normalizacao dias_original=%s",
            dias_treino
        )
        return plano_jsonb  # Retorna sem enriquecimento se nenhum dia é válido

    logger.info(
        "plano.normalizacao_concluida dias_original=%s dias_normalizado=%s",
        dias_treino, dias_treino_normalizados
    )

    # 1. Gerar calendário determinístico
    try:
        calendario = gerar_calendario(
            data_inicio=data_inicio,
            data_prova=data_prova,
            dias_treino=dias_treino_normalizados
        )
        logger.info(
            "plano.calendario_gerado dias_canonicos=%s total_treinos=%d",
            calendario.dias_treino_canonicos, len(calendario.treinos)
        )
    except ValueError as e:
        logger.warning(
            "plano.enriquecimento_falhou_calendario motivo=%s", str(e)
        )
        return plano_jsonb  # Retorna sem enriquecimento se calendário falha

    # 2. Copiar plano para não mutar original
    plano_enriquecido = {}
    for chave, valor in plano_jsonb.items():
        if chave != "treinos":
            plano_enriquecido[chave] = valor

    # 3. Processar treinos
    if "treinos" not in plano_jsonb or not plano_jsonb["treinos"]:
        plano_enriquecido["treinos"] = []
        return plano_enriquecido

    treinos_originais = plano_jsonb["treinos"]
    if not isinstance(treinos_originais, list):
        logger.warning("plano.treinos_nao_e_lista tipo=%s", type(treinos_originais))
        return plano_jsonb

    # Track de quantos treinos de cada dia já foram mapeados
    contadores_por_dia: dict[str, int] = {}
    for dia in calendario.dias_treino_canonicos:
        contadores_por_dia[dia] = 0

    treinos_enriquecidos = []
    for treino_orig in treinos_originais:
        if not isinstance(treino_orig, dict):
            treinos_enriquecidos.append(treino_orig)
            continue

        treino_copia = dict(treino_orig)

        # Obter dia_semana do treino (pode vir como "dia_semana" ou "dia")
        dia_str = treino_copia.get("dia_semana") or treino_copia.get("dia")
        if not dia_str:
            treinos_enriquecidos.append(treino_copia)
            continue

        # Normalizar dia (aceita português, inglês, acentos, abreviações)
        dia_normalizado = _normalizar_dia(str(dia_str))
        if dia_normalizado is None:
            logger.warning(
                "plano.dia_invalido_no_treino dia=%s (nao sera enriquecido)",
                dia_str
            )
            treinos_enriquecidos.append(treino_copia)
            continue

        # Converter para weekday Python
        try:
            weekday = normalizar_dia_da_semana(dia_normalizado)
            dia_canonico = nome_canonico_do_weekday(weekday)
            logger.debug(
                "plano.dia_normalizado entrada=%s weekday=%d canonico=%s",
                dia_str, weekday, dia_canonico
            )
        except ValueError as ve:
            logger.warning(
                "plano.dia_nao_reconhecido dia=%s erro=%s", dia_str, str(ve)
            )
            treinos_enriquecidos.append(treino_copia)
            continue

        # Encontrar N-ésima ocorrência deste dia no calendário
        indice = contadores_por_dia.get(dia_canonico, 0)
        treinos_neste_dia = [
            t for t in calendario.treinos if t.dia_semana == dia_canonico
        ]

        logger.debug(
            "plano.mapeamento_dia dia_canonico=%s indice=%d total_neste_dia=%d "
            "dias_disponveis=%s",
            dia_canonico, indice, len(treinos_neste_dia),
            [t.dia_semana for t in calendario.treinos[:5]]  # primeiros 5 para debug
        )

        if indice < len(treinos_neste_dia):
            treino_calendario = treinos_neste_dia[indice]
            treino_copia["data"] = treino_calendario.data.isoformat()
            contadores_por_dia[dia_canonico] += 1
            logger.info(
                "plano.treino_enriquecido dia=%s data=%s indice=%d",
                dia_canonico, treino_copia["data"], indice
            )
        else:
            logger.warning(
                "plano.dia_sem_mapeamento dia=%s indice=%d total=%d "
                "(nao ha treinos suficientes)",
                dia_canonico, indice, len(treinos_neste_dia)
            )

        treinos_enriquecidos.append(treino_copia)

    plano_enriquecido["treinos"] = treinos_enriquecidos
    return plano_enriquecido


def enriquecer_plano_com_datas(
    plano_jsonb: dict,
    atleta: Atleta,
    data_inicio: Optional[date],
    data_prova: Optional[date],
    dias_treino_json: Optional[list[str]],
    usar_datas_reais: Optional[bool] = None
) -> dict:
    """Enriquece plano com datas reais se flag ativo e dados disponíveis.

    Lógica de flag:
      1. Se usar_datas_reais (param) é explícito, usa esse valor
      2. Senão, usa atleta.usar_datas_reais
      3. Se flag False, retorna plano intocado (versão 1)

    Validação de pré-requisitos:
      - Flag deve estar True
      - data_inicio, data_prova e dias_treino_json devem estar presentes
      - plano deve ter lista "treinos"

    Se qualquer validação falhar, retorna plano original (sem erro).
    """
    # 1. Resolver flag: param > atleta.usar_datas_reais > False
    flag_ativo = (
        usar_datas_reais
        if usar_datas_reais is not None
        else atleta.usar_datas_reais
    )

    # 2. Validar pré-requisitos
    if not flag_ativo:
        logger.debug("plano.enriquecimento_desativado apelido=%s", atleta.apelido)
        return plano_jsonb

    if not data_inicio or not data_prova or not dias_treino_json:
        logger.debug(
            "plano.enriquecimento_dados_incompletos apelido=%s "
            "data_inicio=%s data_prova=%s dias_treino=%s",
            atleta.apelido, data_inicio, data_prova,
            "presente" if dias_treino_json else "ausente"
        )
        return plano_jsonb

    if not isinstance(plano_jsonb, dict) or "treinos" not in plano_jsonb:
        logger.debug(
            "plano.enriquecimento_sem_treinos apelido=%s", atleta.apelido
        )
        return plano_jsonb

    # 3. Enriquecer
    logger.info(
        "plano.enriquecimento_iniciado apelido=%s data_inicio=%s data_prova=%s",
        atleta.apelido, data_inicio, data_prova
    )

    plano_enriquecido = _mapear_treinos_com_datas(
        plano_jsonb, data_inicio, data_prova, dias_treino_json
    )

    logger.info(
        "plano.enriquecimento_concluido apelido=%s", atleta.apelido
    )
    return plano_enriquecido


def criar_plano(
    db: Session,
    atleta: Atleta,
    data: PlanoSemanalCreate,
) -> PlanoSemanal:
    """Cria plano semanal aplicando todas as regras da Fase 1.

    Levanta:
      SobrescritaProtegida: se ja existe plano ativo e novo_ciclo=False.
      ValueError: se o JSONB 'plano' estiver ausente/vazio.
    """
    if data.plano is None or data.plano == {} or data.plano == []:
        raise ValueError("Campo 'plano' e obrigatorio e nao pode estar vazio.")

    plano_ativo_existente = _plano_ativo_de(db, atleta.id)

    if plano_ativo_existente is not None:
        if not data.novo_ciclo:
            logger.warning(
                "plano.criacao_bloqueada apelido=%s atleta_id=%s "
                "plano_ativo_id=%s motivo=novo_ciclo_falso",
                atleta.apelido, atleta.id, plano_ativo_existente.id,
            )
            raise SobrescritaProtegida(
                plano_atual_id=str(plano_ativo_existente.id),
                semana_inicio=str(plano_ativo_existente.semana_inicio),
            )
        # Marca como substituido na MESMA transacao - sem deletar dados.
        plano_ativo_existente.status = STATUS_SUBSTITUIDO
        db.add(plano_ativo_existente)
        logger.info(
            "plano.substituido_para_novo_ciclo apelido=%s atleta_id=%s "
            "plano_substituido_id=%s",
            atleta.apelido, atleta.id, plano_ativo_existente.id,
        )

    # Constroi novo plano (excluindo campos que NAO sao colunas)
    payload = data.model_dump(exclude={"apelido", "novo_ciclo"})
    payload["status"] = data.status or STATUS_ATIVO
    payload["versao_estrutura"] = _detectar_versao_estrutura(data)

    # NOVO: Enriquecer plano com datas se flag ativo (Fase 2, Etapa 1)
    payload["plano"] = enriquecer_plano_com_datas(
        plano_jsonb=payload["plano"],
        atleta=atleta,
        data_inicio=data.data_inicio,
        data_prova=data.data_prova,
        dias_treino_json=data.dias_treino_json,
        usar_datas_reais=None  # Usa flag do atleta (já detectado acima)
    )

    plano = PlanoSemanal(atleta_id=atleta.id, **payload)
    db.add(plano)
    db.flush()  # garante id sem fazer commit

    logger.info(
        "plano.criado apelido=%s atleta_id=%s plano_id=%s "
        "versao_estrutura=%s status=%s novo_ciclo=%s",
        atleta.apelido, atleta.id, plano.id,
        plano.versao_estrutura, plano.status, data.novo_ciclo,
    )

    return plano


def detectar_versao_estrutura(data: PlanoSemanalCreate) -> int:
    """Wrapper publico para teste unitario do detector."""
    return _detectar_versao_estrutura(data)


# ---------------------------------------------------------------------------
# Exceções da lógica adaptativa
# ---------------------------------------------------------------------------

class PlanoAtivoNaoEncontrado(Exception):
    def __init__(self, apelido: str):
        self.apelido = apelido
        super().__init__(f"Atleta '{apelido}' não tem plano ativo.")


# ---------------------------------------------------------------------------
# Helper interno: salvar memória de ajuste/substituição
# ---------------------------------------------------------------------------

def _salvar_memoria_ajuste(
    db: Session,
    atleta: Atleta,
    motivo: str,
    tipo: str = "ajuste_plano",
) -> dict:
    from datetime import date as _date
    from app.services.memoria_service import salvar_memoria as _salvar_memoria

    chave = f"ajuste_plano_{_date.today().isoformat()}"
    dados = AtletaMemoriaCreate(
        tipo=tipo,
        chave=chave,
        valor_texto=motivo,
        origem="feedback_atleta",
        importancia=5,
        confianca=1.0,
    )
    return _salvar_memoria(db, str(atleta.id), dados)


# ---------------------------------------------------------------------------
# Atualização parcial do plano ativo (PATCH)
# ---------------------------------------------------------------------------

def atualizar_plano_ativo(
    db: Session,
    atleta: Atleta,
    dados: Any,  # PlanoSemanalUpdate — import circular evitado com Any
) -> PlanoSemanal:
    """Aplica patch parcial no plano ativo do atleta.

    Levanta PlanoAtivoNaoEncontrado se não houver plano ativo.
    Se dados.motivo_revisao estiver presente e dados.salvar_memoria=True,
    salva memória do tipo ajuste_plano automaticamente.
    """
    plano = _plano_ativo_de(db, atleta.id)
    if plano is None:
        raise PlanoAtivoNaoEncontrado(atleta.apelido)

    campos = dados.model_dump(
        exclude={"motivo_revisao", "salvar_memoria"},
        exclude_unset=True,
    )
    for campo, valor in campos.items():
        setattr(plano, campo, valor)

    db.commit()
    db.refresh(plano)

    if getattr(dados, "motivo_revisao", None) and getattr(dados, "salvar_memoria", True):
        _salvar_memoria_ajuste(db, atleta, dados.motivo_revisao)

    logger.info(
        "plano.atualizado apelido=%s atleta_id=%s plano_id=%s campos=%s",
        atleta.apelido, atleta.id, plano.id, list(campos.keys()),
    )
    return plano


# ---------------------------------------------------------------------------
# Substituição do plano ativo (POST /substituir-atual)
# ---------------------------------------------------------------------------

def substituir_plano_ativo(
    db: Session,
    atleta: Atleta,
    dados: Any,  # SubstituirPlanoPayload — import circular evitado com Any
) -> dict:
    """Marca o plano ativo como substituido e cria novo plano ativo.

    Levanta PlanoAtivoNaoEncontrado se não houver plano ativo.
    Se dados.motivo_substituicao estiver presente, salva memória
    do tipo decisao_treinador automaticamente.

    Retorna dict com plano_anterior, novo_plano e memoria_salva.
    """
    plano_anterior = _plano_ativo_de(db, atleta.id)
    if plano_anterior is None:
        raise PlanoAtivoNaoEncontrado(atleta.apelido)

    plano_anterior.status = STATUS_SUBSTITUIDO
    db.add(plano_anterior)

    payload = dados.model_dump(exclude={"motivo_substituicao"})
    payload["status"] = STATUS_ATIVO
    payload["versao_estrutura"] = dados.versao_estrutura or 2

    novo = PlanoSemanal(atleta_id=atleta.id, **payload)
    db.add(novo)
    db.commit()
    db.refresh(plano_anterior)
    db.refresh(novo)

    memoria = None
    if getattr(dados, "motivo_substituicao", None):
        memoria = _salvar_memoria_ajuste(
            db, atleta, dados.motivo_substituicao, tipo="decisao_treinador"
        )

    logger.info(
        "plano.substituido apelido=%s atleta_id=%s "
        "plano_anterior_id=%s novo_plano_id=%s",
        atleta.apelido, atleta.id, plano_anterior.id, novo.id,
    )
    return {"plano_anterior": plano_anterior, "novo_plano": novo, "memoria_salva": memoria}
