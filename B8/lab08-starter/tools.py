"""Helpers for teaching JSON Schema validation (not a solved lab)."""
from pathlib import Path
import yaml


def get_book_schema(path=None):
    spec_file = Path(path) if path else Path(__file__).parent / "openapi.yaml"
    spec = yaml.safe_load(spec_file.read_text(encoding="utf-8"))
    return spec["components"]["schemas"]["Book"]
