"""Settings loader - reads config/settings.yaml + config/endpoints.yaml into typed objects."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def _load(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


@lru_cache(maxsize=1)
def settings() -> dict:
    return _load(ROOT / "config" / "settings.yaml")


@lru_cache(maxsize=1)
def endpoints() -> dict:
    return _load(ROOT / "config" / "endpoints.yaml")


@lru_cache(maxsize=1)
def sector_map() -> dict:
    return _load(ROOT / "config" / "sector_map.yaml")


def data_path(rel: str) -> Path:
    """Resolve a path relative to the project root (settings store repo-relative paths)."""
    p = Path(rel)
    return p if p.is_absolute() else ROOT / p
