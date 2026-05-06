"""Exporta um OpenAPI compatível com o importador de Actions do Custom GPT.

O FastAPI gera OpenAPI 3.1 por padrão. O importador de Actions costuma aceitar
melhor OpenAPI 3.0.x, especialmente para `components.schemas` com campos
nullable que em 3.1 aparecem como `anyOf: [<schema>, {"type": "null"}]`.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from app.main import app


ROOT = Path(__file__).resolve().parent.parent
OUTFILE = ROOT / "openapi-gpt-actions.json"


def _convert_nullable_anyof(schema: dict[str, Any]) -> dict[str, Any]:
    any_of = schema.get("anyOf")
    if not isinstance(any_of, list) or len(any_of) != 2:
        return schema

    null_branch = None
    other_branch = None
    for item in any_of:
        if isinstance(item, dict) and item.get("type") == "null":
            null_branch = item
        else:
            other_branch = item

    if null_branch is None or not isinstance(other_branch, dict):
        return schema

    converted = {k: v for k, v in schema.items() if k != "anyOf"}

    # Em OpenAPI 3.0, `nullable` funciona melhor com schema inline.
    # Para $ref, usamos allOf para manter compatibilidade.
    if "$ref" in other_branch:
        converted["allOf"] = [{"$ref": other_branch["$ref"]}]
        for key, value in other_branch.items():
            if key != "$ref":
                converted[key] = value
    else:
        for key, value in other_branch.items():
            converted[key] = value

    converted["nullable"] = True
    return converted


def _convert_schema(node: Any) -> Any:
    if isinstance(node, list):
        return [_convert_schema(item) for item in node]

    if not isinstance(node, dict):
        return node

    converted = {key: _convert_schema(value) for key, value in node.items()}
    converted = _convert_nullable_anyof(converted)

    # `type: ["string", "null"]` nao e esperado hoje, mas deixamos defensivo.
    node_type = converted.get("type")
    if isinstance(node_type, list):
        tipos = [item for item in node_type if item != "null"]
        if len(tipos) == 1:
            converted["type"] = tipos[0]
            converted["nullable"] = True

    return converted


def build_schema() -> dict[str, Any]:
    schema = deepcopy(app.openapi())
    schema["openapi"] = "3.0.3"
    schema.pop("jsonSchemaDialect", None)
    return _convert_schema(schema)


def main() -> None:
    schema = build_schema()
    OUTFILE.write_text(
        json.dumps(schema, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
