"""Warm browser upgrades must not mix new markup and indefinitely cached assets."""

import re
from urllib.parse import parse_qs, urlsplit

import pytest


@pytest.mark.parametrize(
    "path",
    [
        "/static/style.css",
        "/static/app.js",
        "/static/styles/scroll-story.css",
        "/static/modules/scroll-story.js",
    ],
)
def test_static_assets_revalidate_on_normal_and_conditional_requests(client, path):
    response = client.get(path)
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-cache"
    assert response.headers["content-security-policy"]
    unchanged = client.get(path, headers={"If-None-Match": response.headers["etag"]})
    assert unchanged.status_code == 304
    assert unchanged.headers["cache-control"] == "no-cache"


def test_html_entrypoints_escape_previous_unversioned_cache(client):
    html = client.get("/").text
    references = re.findall(r'(?:href|src)="(/static/(?:style\.css|app\.js)[^"]*)"', html)
    assert len(references) == 2
    for reference in references:
        assert parse_qs(urlsplit(reference).query).get("v")
        response = client.get(reference)
        assert response.status_code == 200
        assert response.content == client.get(urlsplit(reference).path).content
    # A failed enhancement stays out of the page instead of showing raw copy.
    assert re.search(r'<section[^>]+id="scroll-journey"[^>]+\bhidden\b', html)
