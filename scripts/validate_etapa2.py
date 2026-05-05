#!/usr/bin/env python
"""
Script de validação da Etapa 2 - Contexto por usuário + Consistência.

Executa os 7 cenários QA obrigatórios e gera relatório.
"""

import sys
import os
import json
import uuid
from datetime import date, datetime
from decimal import Decimal

# Setup de paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.models.atleta import Atleta
from app.models.contexto_atleta import ContextoAtleta
from app.services.context_service import (
    salvar_contexto,
    listar_contexto,
    contexto_com_fallback,
    EntradaContexto,
    salvar_contexto_em_lote,
)
from app.services.plano_service import _normalizar_dia


class ValidadorEtapa2:
    """Executor dos 7 cenários QA da Etapa 2."""

    def __init__(self):
        """Inicializa com banco em memória."""
        # Usar SQLite sem schema (não suporta 'public')
        from sqlalchemy.ext.declarative import declarative_base
        self.engine = create_engine("sqlite:///:memory:", echo=False)

        # Criar um novo Base apenas com as tabelas que usamos
        TestBase = declarative_base()

        # Redefini módulos para novo Base
        import app.models.atleta
        import app.models.contexto_atleta
        old_base = app.models.atleta.Base
        app.models.atleta.Base = TestBase
        app.models.contexto_atleta.Base = TestBase

        # Importar modelos
        from app.models.atleta import Atleta as AtletaModel
        from app.models.contexto_atleta import ContextoAtleta as ContextoModel

        # Restaurar Base original
        app.models.atleta.Base = old_base
        app.models.contexto_atleta.Base = old_base

        # Criar tabelas
        TestBase.metadata.create_all(self.engine)
        SessionLocal = sessionmaker(bind=self.engine)
        self.db = SessionLocal()
        self.resultados = []

    def log(self, cenario: str, status: str, mensagem: str = ""):
        """Registra resultado de um cenário."""
        self.resultados.append({
            "cenario": cenario,
            "status": status,
            "mensagem": mensagem,
            "timestamp": datetime.now().isoformat(),
        })
        emoji = "✅" if status == "PASS" else "❌"
        print(f"{emoji} {cenario}: {mensagem}")

    def _criar_atleta(self, apelido: str) -> Atleta:
        """Helper para criar atleta com dados padrão."""
        atleta = Atleta(
            apelido=apelido,
            nome=f"Atleta {apelido}",
            objetivo="21km",
            dias_treino="4",
            pace_confortavel="5:00",
            maior_distancia_recente_km=15.0,
            historico_dores="joelho",
            proxima_prova="Meia Maratona ABC",
            distancia_alvo_km=21.0,
        )
        self.db.add(atleta)
        self.db.commit()
        self.db.refresh(atleta)
        return atleta

    # ========================================================================
    # CENÁRIO 1: WRITE CONTEXTO - Salva corretamente
    # ========================================================================

    def cenario_1_write_contexto(self):
        """Validar que salvar contexto funciona corretamente."""
        try:
            apelido = f"atleta_write_{uuid.uuid4().hex[:8]}"
            atleta = self._criar_atleta(apelido)

            # Salvar contexto
            contexto = salvar_contexto(
                self.db,
                atleta,
                tipo="objetivo",
                chave="dias_treino",
                valor="4",
                origem="teste_qa",
                confianca=1.0,
            )
            self.db.commit()

            # Validar
            assert contexto.tipo == "objetivo"
            assert contexto.chave == "dias_treino"
            assert contexto.valor == "4"
            assert contexto.origem == "teste_qa"

            # Verificar no banco
            persistido = (
                self.db.query(ContextoAtleta)
                .filter(
                    ContextoAtleta.atleta_id == atleta.id,
                    ContextoAtleta.tipo == "objetivo",
                    ContextoAtleta.chave == "dias_treino",
                )
                .first()
            )
            assert persistido is not None
            assert persistido.valor == "4"

            self.log("Cenário 1", "PASS", "Contexto salvo corretamente")
        except Exception as e:
            self.log("Cenário 1", "FAIL", str(e))

    # ========================================================================
    # CENÁRIO 2: UPSERT - Atualiza sem duplicar
    # ========================================================================

    def cenario_2_upsert(self):
        """Validar que UPSERT funciona (atualiza, não duplica)."""
        try:
            apelido = f"atleta_upsert_{uuid.uuid4().hex[:8]}"
            atleta = self._criar_atleta(apelido)

            # Primeira escrita
            ctx1 = salvar_contexto(
                self.db, atleta,
                tipo="objetivo", chave="dias_treino", valor="4",
                origem="primeira", confianca=1.0,
            )
            self.db.commit()
            id1 = ctx1.id

            # Segunda escrita com valor diferente
            ctx2 = salvar_contexto(
                self.db, atleta,
                tipo="objetivo", chave="dias_treino", valor="5",
                origem="segunda", confianca=0.9,
            )
            self.db.commit()
            id2 = ctx2.id

            # Validar: mesmos IDs = atualização
            assert id1 == id2, f"IDs diferentes: {id1} != {id2}"

            # Validar: apenas 1 entrada no banco
            entradas = listar_contexto(self.db, atleta.id)
            assert len(entradas) == 1, f"Esperado 1 entrada, encontrado {len(entradas)}"
            assert entradas[0].valor == "5"
            assert entradas[0].origem == "segunda"

            self.log("Cenário 2", "PASS", "UPSERT funcionando (sem duplicação)")
        except Exception as e:
            self.log("Cenário 2", "FAIL", str(e))

    # ========================================================================
    # CENÁRIO 3: READ - Estrutura correta
    # ========================================================================

    def cenario_3_read(self):
        """Validar que READ retorna estrutura correta."""
        try:
            apelido = f"atleta_read_{uuid.uuid4().hex[:8]}"
            atleta = self._criar_atleta(apelido)

            # Salvar vários contextos
            salvar_contexto(
                self.db, atleta, tipo="objetivo", chave="dias_treino",
                valor="4", origem="teste", confianca=1.0,
            )
            salvar_contexto(
                self.db, atleta, tipo="objetivo", chave="distancia",
                valor="21", origem="teste", confianca=1.0,
            )
            salvar_contexto(
                self.db, atleta, tipo="historico", chave="lesao",
                valor="joelho", origem="teste", confianca=0.8,
            )
            self.db.commit()

            # READ
            entradas = listar_contexto(self.db, atleta.id)
            assert len(entradas) == 3

            # Validar estrutura
            resumo = contexto_com_fallback(self.db, atleta)
            assert "objetivo" in resumo
            assert resumo["objetivo"]["dias_treino"] == "4"
            assert resumo["objetivo"]["distancia"] == "21"
            assert "historico" in resumo
            assert resumo["historico"]["lesao"] == "joelho"

            self.log("Cenário 3", "PASS", "Estrutura de READ correta")
        except Exception as e:
            self.log("Cenário 3", "FAIL", str(e))

    # ========================================================================
    # CENÁRIO 4: DELETE - Remove corretamente
    # ========================================================================

    def cenario_4_delete(self):
        """Validar que DELETE remove corretamente."""
        try:
            apelido = f"atleta_delete_{uuid.uuid4().hex[:8]}"
            atleta = self._criar_atleta(apelido)

            # Salvar
            salvar_contexto(
                self.db, atleta, tipo="objetivo", chave="dias_treino",
                valor="4", origem="teste", confianca=1.0,
            )
            self.db.commit()

            # Verificar que existe
            existente = (
                self.db.query(ContextoAtleta)
                .filter(
                    ContextoAtleta.atleta_id == atleta.id,
                    ContextoAtleta.tipo == "objetivo",
                    ContextoAtleta.chave == "dias_treino",
                )
                .first()
            )
            assert existente is not None

            # DELETE
            deleted = (
                self.db.query(ContextoAtleta)
                .filter(
                    ContextoAtleta.atleta_id == atleta.id,
                    ContextoAtleta.tipo == "objetivo",
                    ContextoAtleta.chave == "dias_treino",
                )
                .delete()
            )
            self.db.commit()
            assert deleted == 1

            # Verificar que foi removido
            gone = (
                self.db.query(ContextoAtleta)
                .filter(
                    ContextoAtleta.atleta_id == atleta.id,
                    ContextoAtleta.tipo == "objetivo",
                    ContextoAtleta.chave == "dias_treino",
                )
                .first()
            )
            assert gone is None

            self.log("Cenário 4", "PASS", "DELETE funcionando corretamente")
        except Exception as e:
            self.log("Cenário 4", "FAIL", str(e))

    # ========================================================================
    # CENÁRIO 5: SESSÃO COM CONTEXTO - Contexto presente
    # ========================================================================

    def cenario_5_sessao_com_contexto(self):
        """Validar que contexto_com_fallback retorna contexto se existir."""
        try:
            apelido = f"atleta_sessao_com_{uuid.uuid4().hex[:8]}"
            atleta = self._criar_atleta(apelido)

            # Salvar contexto
            salvar_contexto(
                self.db, atleta, tipo="objetivo", chave="dias_treino",
                valor="4", origem="teste", confianca=1.0,
            )
            salvar_contexto(
                self.db, atleta, tipo="historico", chave="lesao",
                valor="joelho", origem="teste", confianca=0.8,
            )
            self.db.commit()

            # Chamar fallback
            resultado = contexto_com_fallback(self.db, atleta)

            # Validar
            assert "objetivo" in resultado
            assert resultado["objetivo"]["dias_treino"] == "4"
            assert "historico" in resultado
            assert resultado["historico"]["lesao"] == "joelho"

            self.log("Cenário 5", "PASS", "Contexto_resumo presente e correto")
        except Exception as e:
            self.log("Cenário 5", "FAIL", str(e))

    # ========================================================================
    # CENÁRIO 6: SESSÃO SEM CONTEXTO - Fallback funciona
    # ========================================================================

    def cenario_6_sessao_sem_contexto_fallback(self):
        """Validar que contexto_com_fallback retorna fallback se não há contexto."""
        try:
            apelido = f"atleta_fallback_{uuid.uuid4().hex[:8]}"
            # Criar atleta COM dados de perfil
            atleta = Atleta(
                apelido=apelido,
                nome="Atleta Fallback",
                objetivo="Meia Maratona",
                dias_treino="3",
                pace_confortavel="5:30",
                historico_dores="tornozelo",
                proxima_prova="Meia ABC",
                distancia_alvo_km=21.0,
            )
            self.db.add(atleta)
            self.db.commit()

            # NÃO salvar contexto explicitamente

            # Chamar fallback
            resultado = contexto_com_fallback(self.db, atleta)

            # Validar que não está vazio
            assert resultado != {}, "Fallback não deveria retornar dict vazio"

            # Validar que tem dados do atleta
            assert len(resultado) > 0, "Fallback deveria gerar contexto"

            self.log("Cenário 6", "PASS", "Fallback funcionando (contexto não vazio)")
        except Exception as e:
            self.log("Cenário 6", "FAIL", str(e))

    # ========================================================================
    # CENÁRIO 7: CONSISTÊNCIA DE DIAS - Normaliza saída
    # ========================================================================

    def cenario_7_consistencia_dias(self):
        """Validar normalização de dias (inglês/acentos -> forma canônica)."""
        try:
            # Testar normalizador direto
            casos = [
                ("Tuesday", "terca"),
                ("terça", "terca"),
                ("Quinta", "quinta"),
                ("monday", "segunda"),
                ("Mon", "segunda"),
                ("seg", "segunda"),
            ]

            for entrada, esperado in casos:
                resultado = _normalizar_dia(entrada)
                assert resultado == esperado, \
                    f"Normalização falhou: {entrada} -> {resultado} (esperado {esperado})"

            self.log("Cenário 7", "PASS", "Dias normalizados corretamente")
        except Exception as e:
            self.log("Cenário 7", "FAIL", str(e))

    # ========================================================================
    # EXECUTOR E RELATÓRIO
    # ========================================================================

    def executar_todos(self):
        """Executa todos os 7 cenários."""
        print("\n" + "="*70)
        print("🚀 VALIDAÇÃO ETAPA 2 - CONTEXTO POR USUÁRIO + CONSISTÊNCIA")
        print("="*70 + "\n")

        self.cenario_1_write_contexto()
        self.cenario_2_upsert()
        self.cenario_3_read()
        self.cenario_4_delete()
        self.cenario_5_sessao_com_contexto()
        self.cenario_6_sessao_sem_contexto_fallback()
        self.cenario_7_consistencia_dias()

        self._relatorio_final()

    def _relatorio_final(self):
        """Gera relatório final."""
        print("\n" + "="*70)
        print("📊 RELATÓRIO FINAL")
        print("="*70 + "\n")

        passed = sum(1 for r in self.resultados if r["status"] == "PASS")
        failed = sum(1 for r in self.resultados if r["status"] == "FAIL")
        total = len(self.resultados)

        for resultado in self.resultados:
            status_str = "✅ PASS" if resultado["status"] == "PASS" else "❌ FAIL"
            print(f"{status_str}: {resultado['cenario']}")
            if resultado['mensagem']:
                print(f"         {resultado['mensagem']}")

        print(f"\n{'─'*70}")
        print(f"Total: {total} cenários")
        print(f"✅ Aprovados: {passed}")
        print(f"❌ Reprovados: {failed}")
        print(f"Taxa de sucesso: {passed/total*100:.1f}%")
        print(f"{'─'*70}\n")

        # Salvar JSON
        with open("etapa2_validation_report.json", "w", encoding="utf-8") as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "total": total,
                    "passed": passed,
                    "failed": failed,
                    "resultados": self.resultados,
                },
                f, indent=2, ensure_ascii=False,
            )
        print("📄 Relatório salvo em: etapa2_validation_report.json\n")

        return failed == 0


if __name__ == "__main__":
    validador = ValidadorEtapa2()
    sucesso = validador.executar_todos()
    sys.exit(0 if sucesso else 1)
