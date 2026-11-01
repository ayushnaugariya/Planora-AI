"""WCAG AA colour contrast for shared text tokens and landmark/ARIA guarantees in static pages."""

import re
from pathlib import Path

import pytest

STATIC = Path(__file__).resolve().parents[2] / "frontend"
STYLES = STATIC / "styles"


def luminance(hex_color: str) -> float:
    channels = [int(hex_color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast(foreground: str, background: str) -> float:
    high, low = sorted((luminance(foreground), luminance(background)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def token(name: str) -> str:
    match = re.search(rf"--{name}:(#[0-9a-fA-F]{{6}})", (STYLES / "tokens.css").read_text(encoding="utf-8"))
    assert match, name
    return match.group(1)


LIGHT_SURFACES = ["#fbf8f2", "#fffefa", "#ffffff", "#f0ede5", "#f2ede3", "#edf0ea", "#f3eef7"]


@pytest.mark.parametrize("text_token", ["violet", "muted", "ink", "navy"])
def test_text_tokens_meet_aa_on_light_surfaces(text_token):
    for surface in [*LIGHT_SURFACES, token("violet-soft")]:
        assert contrast(token(text_token), surface) >= 4.5, (text_token, surface)


@pytest.mark.parametrize(
    ("css_file", "selector", "minimum"),
    [
        ("landing.css", r"\.value-strip i\{[^}]*color:(#[0-9a-f]{6})", 4.5),
        ("workspace.css", r"\.event-card-number\{[^}]*color:(#[0-9a-f]{6})", 3.0),  # 30px large text
        ("workspace.css", r"\.c1\{background:(#[0-9a-f]{6})", 4.5),  # white chart label text
        ("workspace.css", r"\.c4\{background:(#[0-9a-f]{6})", 4.5),
    ],
)
def test_specific_colours_meet_aa(css_file, selector, minimum):
    color = re.search(selector, (STYLES / css_file).read_text(encoding="utf-8")).group(1)
    background = "#fbf8f2" if "value-strip" in selector else "#ffffff"
    assert contrast(color, background) >= minimum


def test_every_static_page_exposes_one_main_landmark():
    for page in ("index.html", "invitation.html", "invitation-unavailable.html", "api-docs.html"):
        html = (STATIC / page).read_text(encoding="utf-8")
        assert re.search(r'<main\b|role="main"', html), page


def test_decorative_glyphs_are_hidden_from_assistive_technology():
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    assert "<i>/</i>" not in html
    assert html.count('<i aria-hidden="true">/</i>') == 3
    assert "'aria-hidden':'true'" in (STATIC / "modules" / "shell.js").read_text(encoding="utf-8")


def test_api_docs_load_local_contrast_overrides(client):
    html = client.get("/api/docs").text
    assert '<link rel="stylesheet" href="/static/api-docs.css">' in html
    css = client.get("/static/api-docs.css")
    assert css.status_code == 200
    for method, color in re.findall(
        r"opblock-(\w+) \.opblock-summary-method \{ background: (#[0-9a-f]{6})", css.text
    ):
        assert contrast("#ffffff", color) >= 4.5, method
