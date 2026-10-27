"""Static checks that keep the frontend compatible with the strict CSP."""

import re
from pathlib import Path

STATIC = Path(__file__).resolve().parents[2] / "frontend"
HTML = (STATIC / "index.html").read_text()
JS = (STATIC / "app.js").read_text()


def test_no_inline_scripts_or_handlers():
    assert not re.search(r"<script(?![^>]*\bsrc=)[^>]*>", HTML)
    assert not re.search(r"\son(click|load|submit|change)\s*=", HTML, re.I)


def test_no_inline_style_blocks_or_attributes():
    assert "<style" not in HTML
    assert not re.search(r"\sstyle\s*=", HTML)


def test_js_never_uses_innerhtml_or_eval():
    assert "innerHTML" not in JS
    assert "outerHTML" not in JS
    assert "insertAdjacentHTML" not in JS
    assert not re.search(r"\beval\(|new Function\(", JS)


def test_accessibility_basics():
    assert '<html lang="en">' in HTML
    assert 'class="skip"' in HTML
    assert 'role="tablist"' in HTML and 'role="tabpanel"' in HTML
    assert 'aria-live="polite"' in HTML
    # every form control has an associated label
    ids = re.findall(r'<(?:input|select|textarea)[^>]*\bid="([^"]+)"', HTML)
    for i in ids:
        assert f'for="{i}"' in HTML, f"missing label for #{i}"
