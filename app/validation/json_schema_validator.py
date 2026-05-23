import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

PROJECT_SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schemas"


def schema_path_for(request_type: str) -> Path:
    return PROJECT_SCHEMA_DIR / f"{request_type}.schema.json"


def validate_payload(request_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    path = schema_path_for(request_type)
    with path.open("r", encoding="utf-8") as handle:
        schema = json.load(handle)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(payload), key=lambda err: list(err.path))
    if errors:
        return {
            "valid": False,
            "errors": [
                {"path": ".".join(str(part) for part in error.path), "message": error.message}
                for error in errors
            ],
        }
    return {"valid": True, "errors": []}
