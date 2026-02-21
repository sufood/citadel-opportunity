import json
from pathlib import Path

from app.config import get_settings


def _base_dir() -> Path:
    return get_settings().tmp_dir


def create_atm_dir(uuid: str) -> Path:
    """Create and return the tmp/{uuid}/ directory."""
    path = _base_dir() / uuid
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_json(uuid: str, filename: str, data: dict) -> Path:
    """Write data as indented JSON to tmp/{uuid}/{filename}."""
    dir_path = create_atm_dir(uuid)
    file_path = dir_path / filename
    file_path.write_text(json.dumps(data, indent=2, default=str))
    return file_path


def read_json(uuid: str, filename: str) -> dict | None:
    """Read JSON from tmp/{uuid}/{filename}, or None if missing."""
    file_path = _base_dir() / uuid / filename
    if not file_path.exists():
        return None
    return json.loads(file_path.read_text())


def list_atm_dirs() -> list[str]:
    """Return all UUID subdirectory names in tmp/."""
    base = _base_dir()
    if not base.exists():
        return []
    return sorted(d.name for d in base.iterdir() if d.is_dir() and not d.name.startswith("."))


def list_files(uuid: str) -> list[str]:
    """Return all filenames in tmp/{uuid}/."""
    dir_path = _base_dir() / uuid
    if not dir_path.exists():
        return []
    return sorted(f.name for f in dir_path.iterdir() if f.is_file())
