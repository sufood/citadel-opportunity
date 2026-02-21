import os
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import ValidationError


def test_settings_loads_from_env():
    env = {
        "TENDERS_USERNAME": "testuser",
        "TENDERS_PASSWORD": "testpass",
        "TMP_DIR": "/tmp/test",
        "BROWSER_HEADLESS": "false",
    }
    with patch.dict(os.environ, env, clear=False):
        from app.config import Settings

        s = Settings()
        assert s.tenders_username == "testuser"
        assert s.tenders_password == "testpass"
        assert s.tmp_dir == Path("/tmp/test")
        assert s.browser_headless is False


def test_settings_defaults():
    env = {
        "TENDERS_USERNAME": "user",
        "TENDERS_PASSWORD": "pass",
    }
    with patch.dict(os.environ, env, clear=False):
        from app.config import Settings

        s = Settings()
        assert s.tmp_dir == Path("./tmp")
        assert s.browser_headless is True


def test_settings_missing_required():
    with patch.dict(os.environ, {}, clear=True):
        from app.config import Settings

        with pytest.raises(ValidationError):
            Settings(_env_file=None)
