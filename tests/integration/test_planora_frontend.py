"""All new modules retain CSP-safe DOM rendering and locally served dependencies."""

import re
from pathlib import Path
from urllib.parse import urlsplit

from app.main import app

FRONTEND = Path(__file__).resolve().parents[2] / "frontend"


def test_every_module_uses_safe_dom_and_resolvable_local_imports():
    for path in FRONTEND.rglob("*.js"):
        source = path.read_text(encoding="utf-8")
        for forbidden in ("innerHTML", "outerHTML", "insertAdjacentHTML"):
            assert forbidden not in source, path
        assert not re.search(r"\beval\(|new Function\(", source), path
        for reference in re.findall(r"from\s+['\"]([^'\"]+)['\"]", source):
            target = (
                FRONTEND / reference.removeprefix("/static/")
                if reference.startswith("/static/")
                else path.parent / reference
            )
            assert target.is_file(), (path, reference)


def test_new_routes_and_strict_dtos_are_additive():
    contract = app.openapi()
    for path, method in [
        ("/api/events/{event_id}/rescue", "post"),
        ("/api/events/{event_id}/vendors/{vendor_id}", "patch"),
        ("/api/demo", "get"),
    ]:
        assert method in contract["paths"][path]
    for name in ("RescueRequest", "ReplacementQuote", "VendorUpdate"):
        assert contract["components"]["schemas"][name]["additionalProperties"] is False


def test_all_stylesheet_and_artwork_paths_are_local_and_resolve():
    source = (FRONTEND / "index.html").read_text(encoding="utf-8")
    for reference in re.findall(r'(?:href|src)="(/static/[^\"]+)"', source):
        assert (FRONTEND / urlsplit(reference).path.removeprefix("/static/")).is_file()
    for stylesheet in FRONTEND.rglob("*.css"):
        for reference in re.findall(r"url\(['\"]?([^'\")]+)", stylesheet.read_text(encoding="utf-8-sig")):
            assert reference.startswith("/static/")
            assert (FRONTEND / reference.removeprefix("/static/")).is_file()
