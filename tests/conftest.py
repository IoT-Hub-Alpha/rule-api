from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


@pytest.fixture()
def app(tmp_path_factory, monkeypatch):
    db_path = tmp_path_factory.mktemp("db") / "rule_api_test.db"
    monkeypatch.setenv("RULE_API_DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("RULE_API_CREATE_TABLES", "true")
    monkeypatch.setenv("RULE_API_SQL_ECHO", "false")

    from app.core import main as main_module

    importlib.reload(main_module)
    return main_module.app


@pytest.fixture()
def client(app):
    return TestClient(app)
