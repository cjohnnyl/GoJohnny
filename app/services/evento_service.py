"""Serviço de eventos de treino — ETAPA 3, FASE 3.1.

Transforma planos estruturados em eventos de calendário.
Usa datas do plano (ETAPA 1) + contexto do usuário (ETAPA 2).
"""

import logging
from datetime import date, time, datetime
from typing import Optional, Any, Dict, List
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.atleta import Atleta
from app.models.plano_semanal import PlanoSemanal
from app.schemas.evento import EventoTreinoRead, CalendarioPreview
from app.services.context_service import contexto_com_fallback

logger = logging.getLogger("gojohnny.evento_service")


def _extrair_horario_preferido(contexto: Dict[str, Any]) -> time:
    """Extrai horário preferido do contexto ou retorna padrão (07:00).

    Busca em contexto["preferencia"]["horario_preferido"].
    Esperado formato: "07:00" ou "07:30".
    """
    if not contexto:
        return time(7, 0)

    # Navegar na estrutura: contexto -> preferencia -> horario_preferido
    preferencia = contexto.get("preferencia", {})
    horario_str = preferencia.get("horario_preferido")

    if not horario_str:
        return time(7, 0)

    try:
        # Tentar parseiar "07:00"
        partes = str(horario_str).split(":")
        if len(partes) >= 2:
            hora = int(partes[0])
            minuto = int(partes[1])
            return time(hora, minuto)
    except (ValueError, AttributeError):
        logger.warning("evento.horario_invalido_no_contexto valor=%s", horario_str)
        return time(7, 0)

    return time(7, 0)


def _estimar_duracao_treino(tipo_treino: Optional[str], distancia_km: Optional[float]) -> int:
    """Estima duração do treino em minutos baseado em tipo e distância.

    Heurística:
    - Leve: 50-70 min
    - Moderado: 60-90 min
    - Intenso: 45-75 min
    - Longa: 90-180 min
    - Fallback: 60 min
    """
    tipo = str(tipo_treino).lower() if tipo_treino else ""

    # Se temos distância, usar como proxy (5 min/km em média)
    if distancia_km:
        try:
            duracao = int(float(distancia_km) * 6)  # ~6 min/km em média
            duracao = max(30, min(180, duracao))  # Clamp entre 30-180 min
            return duracao
        except (ValueError, TypeError):
            pass

    # Fallback por tipo
    if "leve" in tipo or "easy" in tipo:
        return 60
    elif "longa" in tipo or "long" in tipo:
        return 120
    elif "intenso" in tipo or "intense" in tipo or "tempo" in tipo:
        return 60
    elif "intervalo" in tipo or "interval" in tipo:
        return 50

    return 60  # Padrão


def _construir_titulo_evento(tipo_treino: Optional[str]) -> str:
    """Constrói título do evento baseado no tipo."""
    tipo = str(tipo_treino).lower() if tipo_treino else "Treino"

    titulos = {
        "leve": "Treino Leve",
        "easy": "Treino Leve",
        "moderado": "Treino Moderado",
        "moderate": "Treino Moderado",
        "intenso": "Treino Intenso",
        "intense": "Treino Intenso",
        "longa": "Longa Distância",
        "long": "Longa Distância",
        "tempo": "Tempo Trial",
        "intervalo": "Treino de Intervalo",
        "interval": "Treino de Intervalo",
    }

    for chave, titulo in titulos.items():
        if chave in tipo:
            return titulo

    return f"Treino - {tipo_treino}" if tipo_treino else "Treino"


def _construir_descricao_evento(
    tipo_treino: Optional[str],
    distancia_km: Optional[float],
    dia_semana: Optional[str]
) -> str:
    """Constrói descrição detalhada do evento."""
    partes = []

    if distancia_km:
        partes.append(f"{distancia_km}km")

    if tipo_treino:
        partes.append(f"{tipo_treino}")

    descricao = " - ".join(partes) if partes else "Treino"

    if dia_semana:
        descricao += f" ({dia_semana.capitalize()})"

    return descricao


def gerar_eventos_treino(
    plano: Dict[str, Any],
    contexto: Optional[Dict[str, Any]] = None,
    data_inicio_override: Optional[date] = None
) -> List[EventoTreinoRead]:
    """Transforma plano em lista de eventos de treino.

    Lê treinos do plano_jsonb['treinos'] e gera eventos estruturados.
    Usa contexto do usuário para horário preferido e ajustes.

    Args:
        plano: Dict com chave "treinos" (lista de treinos)
        contexto: Contexto do usuário com preferências (opcional)
        data_inicio_override: Sobrescrever data_inicio se necessário

    Returns:
        Lista de EventoTreinoRead ordenados por data
    """
    eventos: List[EventoTreinoRead] = []

    if not plano or not isinstance(plano, dict):
        logger.warning("evento.plano_invalido tipo=%s", type(plano))
        return eventos

    treinos = plano.get("treinos", [])
    if not isinstance(treinos, list):
        logger.warning("evento.treinos_nao_e_lista tipo=%s", type(treinos))
        return eventos

    # Extrair horário preferido do contexto
    horario_preferido = _extrair_horario_preferido(contexto)
    logger.info("evento.gerando_eventos_count=%d horario=%s", len(treinos), horario_preferido)

    for idx, treino in enumerate(treinos):
        if not isinstance(treino, dict):
            logger.warning("evento.treino_nao_e_dict idx=%d tipo=%s", idx, type(treino))
            continue

        # Extrair campos do treino
        tipo_treino = treino.get("tipo")
        distancia_km = treino.get("distancia_km") or treino.get("distancia")
        dia_semana = treino.get("dia_semana") or treino.get("dia")

        # Data pode vir do treino enriquecido (ETAPA 1) ou usar fallback
        data_treino_str = treino.get("data")
        if data_treino_str:
            try:
                if isinstance(data_treino_str, str):
                    data_treino = date.fromisoformat(data_treino_str)
                else:
                    data_treino = data_treino_str
            except (ValueError, AttributeError):
                logger.warning("evento.data_invalida_no_treino valor=%s", data_treino_str)
                continue
        else:
            logger.warning("evento.treino_sem_data idx=%d", idx)
            continue

        # Construir evento
        evento = EventoTreinoRead(
            titulo=_construir_titulo_evento(tipo_treino),
            descricao=_construir_descricao_evento(tipo_treino, distancia_km, dia_semana),
            data=data_treino,
            hora=horario_preferido,
            duracao_min=_estimar_duracao_treino(tipo_treino, distancia_km)
        )
        eventos.append(evento)
        logger.debug(
            "evento.criado titulo=%s data=%s hora=%s duracao=%d",
            evento.titulo, evento.data, evento.hora, evento.duracao_min
        )

    # Ordenar por data
    eventos.sort(key=lambda e: e.data)

    logger.info("evento.geracao_concluida total=%d", len(eventos))
    return eventos


def listar_eventos_atleta(
    db: Session,
    atleta: Atleta,
    usar_fallback_contexto: bool = True
) -> CalendarioPreview:
    """Lista eventos do plano ativo do atleta.

    Busca plano ativo + contexto do atleta e gera preview de calendário.

    Args:
        db: Session
        atleta: Atleta objeto
        usar_fallback_contexto: Se True, usa contexto com fallback

    Returns:
        CalendarioPreview com lista de eventos
    """
    # Buscar plano ativo
    plano_ativo = (
        db.query(PlanoSemanal)
        .filter(
            PlanoSemanal.atleta_id == atleta.id,
            PlanoSemanal.status == "ativo"
        )
        .order_by(PlanoSemanal.semana_inicio.desc())
        .first()
    )

    if not plano_ativo or not plano_ativo.plano:
        logger.info("evento.nenhum_plano_ativo atleta_id=%s", atleta.id)
        return CalendarioPreview(
            atleta_apelido=atleta.apelido,
            total_eventos=0,
            eventos=[]
        )

    # Buscar contexto
    contexto = None
    if usar_fallback_contexto:
        contexto = contexto_com_fallback(db, atleta)

    # Gerar eventos
    eventos = gerar_eventos_treino(
        plano_ativo.plano,
        contexto,
        data_inicio_override=plano_ativo.data_inicio
    )

    periodo_inicio = eventos[0].data if eventos else None
    periodo_fim = eventos[-1].data if eventos else None

    return CalendarioPreview(
        atleta_apelido=atleta.apelido,
        total_eventos=len(eventos),
        eventos=eventos,
        periodo_inicio=periodo_inicio,
        periodo_fim=periodo_fim
    )
