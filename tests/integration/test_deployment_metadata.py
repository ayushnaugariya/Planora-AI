"""Runtime dependency discovery must agree for pip/Docker and Vercel's TOML selection."""

import tomllib
from importlib import import_module
from pathlib import Path

from app.main import app

ROOT = Path(__file__).resolve().parents[2]


def test_pyproject_declares_the_existing_runtime_requirements():
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    requirements = [
        line.strip()
        for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    assert metadata["project"].get("dependencies", []) == requirements


def test_vercel_entrypoint_resolves_original_app_and_keeps_static_middleware():
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    module, attribute = metadata["tool"]["vercel"]["entrypoint"].split(":")
    assert getattr(import_module(module), attribute) is app
    static = metadata["tool"]["vercel"]["fastapi"]["static"]
    assert static == {"cdn": False, "exclude": False}
