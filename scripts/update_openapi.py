#!/usr/bin/env python3
"""Atualizar OpenAPI com novos endpoints de memória."""

import json
import sys

try:
    # Ler OpenAPI
    with open('openapi-gpt-actions.json', 'r', encoding='utf-8') as f:
        openapi = json.load(f)

    # Novos paths
    new_paths = {
        "/memorias/{apelido}": {
            "post": {
                "operationId": "salvarMemoria",
                "summary": "Salvar memória do atleta",
                "description": "Salva memória útil evitando duplicatas",
                "tags": ["Memórias"],
                "parameters": [{
                    "name": "apelido",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"},
                    "description": "Apelido do atleta"
                }],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/AtletaMemoriaCreate"}
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Memória salva",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "string"},
                                        "status": {"type": "string"},
                                        "memoria": {"$ref": "#/components/schemas/AtletaMemoriaRead"}
                                    }
                                }
                            }
                        }
                    },
                    "404": {"description": "Atleta não encontrado"}
                }
            }
        },
        "/memorias/{apelido}/resumo": {
            "get": {
                "operationId": "buscarResumoMemorias",
                "summary": "Buscar resumo de memórias",
                "description": "Retorna memórias mais importantes e recentes",
                "tags": ["Memórias"],
                "parameters": [
                    {"name": "apelido", "in": "path", "required": True, "schema": {"type": "string"}},
                    {"name": "limite", "in": "query", "required": False, "schema": {"type": "integer", "default": 20}},
                    {"name": "tipo", "in": "query", "required": False, "schema": {"type": "string"}}
                ],
                "responses": {
                    "200": {"description": "Resumo", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/MemoriasResumoResponse"}}}},
                    "404": {"description": "Atleta não encontrado"}
                }
            }
        },
        "/memorias/{apelido}/buscar": {
            "get": {
                "operationId": "buscarMemorias",
                "summary": "Buscar memórias por texto",
                "description": "Busca memórias relevantes por texto",
                "tags": ["Memórias"],
                "parameters": [
                    {"name": "apelido", "in": "path", "required": True, "schema": {"type": "string"}},
                    {"name": "q", "in": "query", "required": True, "schema": {"type": "string"}},
                    {"name": "limite", "in": "query", "required": False, "schema": {"type": "integer", "default": 20}}
                ],
                "responses": {
                    "200": {"description": "Resultados", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/BuscaMemorias"}}}},
                    "404": {"description": "Atleta não encontrado"}
                }
            }
        },
        "/memorias/{apelido}/resumo-semanal": {
            "post": {
                "operationId": "salvarResumoSemanal",
                "summary": "Salvar resumo semanal",
                "description": "Registra resumo fechado da semana",
                "tags": ["Memórias"],
                "parameters": [{"name": "apelido", "in": "path", "required": True, "schema": {"type": "string"}}],
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ResumoSemanalCreate"}}}
                },
                "responses": {
                    "200": {"description": "Salvo", "content": {"application/json": {"schema": {"type": "object", "properties": {"id": {"type": "string"}, "status": {"type": "string"}, "memoria": {"$ref": "#/components/schemas/AtletaMemoriaRead"}}}}}},
                    "404": {"description": "Atleta não encontrado"}
                }
            }
        }
    }

    # Novos schemas
    new_schemas = {
        "AtletaMemoriaCreate": {
            "type": "object",
            "properties": {
                "tipo": {"type": "string"},
                "chave": {"type": "string"},
                "valor_texto": {"type": "string"},
                "valor_json": {"type": "object"},
                "origem": {"type": "string"},
                "importancia": {"type": "integer", "minimum": 1, "maximum": 5, "default": 3},
                "confianca": {"type": "number", "minimum": 0, "maximum": 1, "default": 1.0},
                "semana_inicio": {"type": "string", "format": "date"}
            },
            "required": ["tipo", "chave", "origem"]
        },
        "AtletaMemoriaRead": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "format": "uuid"},
                "atleta_id": {"type": "string", "format": "uuid"},
                "tipo": {"type": "string"},
                "chave": {"type": "string"},
                "valor_texto": {"type": "string"},
                "valor_json": {"type": "object"},
                "origem": {"type": "string"},
                "importancia": {"type": "integer"},
                "confianca": {"type": "number"},
                "semana_inicio": {"type": "string", "format": "date"},
                "ativo": {"type": "boolean"},
                "criado_em": {"type": "string", "format": "date-time"},
                "atualizado_em": {"type": "string", "format": "date-time"}
            }
        },
        "ResumoSemanalCreate": {
            "type": "object",
            "properties": {
                "semana_inicio": {"type": "string", "format": "date"},
                "resumo": {"type": "string"},
                "aderencia": {"type": "string", "enum": ["parcial", "normal", "excelente"], "default": "normal"},
                "pontos_positivos": {"type": "array", "items": {"type": "string"}},
                "pontos_atencao": {"type": "array", "items": {"type": "string"}},
                "decisoes_treinador": {"type": "array", "items": {"type": "string"}},
                "proximo_foco": {"type": "string"}
            },
            "required": ["semana_inicio", "resumo"]
        },
        "MemoriasResumoResponse": {
            "type": "object",
            "properties": {
                "apelido": {"type": "string"},
                "memorias": {"type": "array", "items": {"$ref": "#/components/schemas/AtletaMemoriaRead"}}
            }
        },
        "BuscaMemorias": {
            "type": "object",
            "properties": {
                "resultados": {"type": "array", "items": {"$ref": "#/components/schemas/AtletaMemoriaRead"}},
                "total": {"type": "integer"}
            }
        }
    }

    # Merge
    openapi["paths"].update(new_paths)
    openapi["components"]["schemas"].update(new_schemas)

    # Salvar
    with open('openapi-gpt-actions.json', 'w', encoding='utf-8') as f:
        json.dump(openapi, f, indent=2, ensure_ascii=False)

    print("OK: OpenAPI atualizado!")
    print(f"  Total de paths: {len(openapi['paths'])}")
    print(f"  Total de schemas: {len(openapi['components']['schemas'])}")

except Exception as e:
    print(f"Erro: {e}", file=sys.stderr)
    sys.exit(1)
