from __future__ import annotations

import json
from pathlib import Path

from src.app_backend.main import app  # matches your src-based layout


def export_openapi_json(output_path: str | Path = "openapi.json") -> Path:
    """
    Export the FastAPI-generated OpenAPI schema to a JSON file.

    Usage:
        uv run python -m src.app_backend.openapi_export
    """
    schema = app.openapi()
    path = Path(output_path)
    path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
    return path


if __name__ == "__main__":
    out = export_openapi_json()
    print(f"OpenAPI schema written to {out}")
