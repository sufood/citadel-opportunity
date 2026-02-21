import json
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def tmp_dir(tmp_path: Path):
    """Patch get_settings to use a temp directory."""
    mock_settings = type("S", (), {"tmp_dir": tmp_path})()
    with patch("app.services.storage.get_settings", return_value=mock_settings):
        yield tmp_path


def test_create_atm_dir(tmp_dir: Path):
    from app.services.storage import create_atm_dir

    uuid = "abc-123"
    result = create_atm_dir(uuid)
    assert result == tmp_dir / uuid
    assert result.is_dir()


def test_create_atm_dir_idempotent(tmp_dir: Path):
    from app.services.storage import create_atm_dir

    uuid = "abc-123"
    create_atm_dir(uuid)
    result = create_atm_dir(uuid)
    assert result.is_dir()


def test_write_json(tmp_dir: Path):
    from app.services.storage import write_json

    uuid = "abc-123"
    data = {"key": "value", "num": 42}
    path = write_json(uuid, "test.json", data)

    assert path.exists()
    content = json.loads(path.read_text())
    assert content == data


def test_read_json(tmp_dir: Path):
    from app.services.storage import read_json, write_json

    uuid = "abc-123"
    data = {"hello": "world"}
    write_json(uuid, "data.json", data)

    result = read_json(uuid, "data.json")
    assert result == data


def test_read_json_missing(tmp_dir: Path):
    from app.services.storage import read_json

    result = read_json("nonexistent", "missing.json")
    assert result is None


def test_list_atm_dirs_empty(tmp_dir: Path):
    from app.services.storage import list_atm_dirs

    assert list_atm_dirs() == []


def test_list_atm_dirs(tmp_dir: Path):
    from app.services.storage import create_atm_dir, list_atm_dirs

    create_atm_dir("uuid-1")
    create_atm_dir("uuid-2")
    # Hidden dirs should be excluded
    (tmp_dir / ".auth_state").mkdir()

    result = list_atm_dirs()
    assert result == ["uuid-1", "uuid-2"]


def test_list_files(tmp_dir: Path):
    from app.services.storage import create_atm_dir, list_files

    uuid = "abc-123"
    d = create_atm_dir(uuid)
    (d / "data-layer.json").write_text("{}")
    (d / "atm-details.json").write_text("{}")

    result = list_files(uuid)
    assert result == ["atm-details.json", "data-layer.json"]


def test_list_files_missing_dir(tmp_dir: Path):
    from app.services.storage import list_files

    assert list_files("nonexistent") == []
