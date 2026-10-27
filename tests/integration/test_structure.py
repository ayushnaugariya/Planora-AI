"""Refactor contracts: actual HTTP assets, unchanged APIs and storage path semantics."""

from pathlib import Path

import pytest

from app.core.config import FRONTEND_DIR, PROJECT_ROOT, database_path
from scripts.check_structure import check_structure


def test_pre_refactor_http_contract_and_import_graph():
    assert check_structure() > 0


@pytest.mark.parametrize("override", [None, "relative/events.sqlite3", "absolute"])
def test_database_path_is_independent_of_asset_location_and_preserves_overrides(
    tmp_path, monkeypatch, override
):
    monkeypatch.chdir(tmp_path)
    if override is None:
        monkeypatch.delenv("EVENTRA_DB_PATH", raising=False)
        assert Path(database_path()) == PROJECT_ROOT / "data/eventra.sqlite3"
    else:
        configured = str(tmp_path / "existing.sqlite3") if override == "absolute" else override
        monkeypatch.setenv("EVENTRA_DB_PATH", configured)
        assert database_path() == configured
    assert not list(tmp_path.glob("*.sqlite3"))  # Resolving configuration never opens storage.


@pytest.mark.parametrize(
    "url,name", [("/", "index.html"), ("/static/app.js", "app.js"), ("/static/style.css", "style.css")]
)
def test_original_asset_urls_serve_relocated_files_from_another_cwd(client, tmp_path, monkeypatch, url, name):
    monkeypatch.chdir(tmp_path)
    response = client.get(url)
    assert response.status_code == 200
    assert response.content == (FRONTEND_DIR / name).read_bytes()
