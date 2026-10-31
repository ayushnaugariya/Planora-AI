"""API documentation must render with the unchanged strict CSP and no CDN."""

from html.parser import HTMLParser

from app.core.security import SECURITY_HEADERS


class Assets(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []
        self.inline = False

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag in {"script", "link"}:
            url = values.get("src" if tag == "script" else "href", "")
            if tag == "script" and not url:
                self.inline = True
            if url:
                self.urls.append(url)


def test_docs_assets_are_local_and_bootstrap_is_external_under_strict_csp(client):
    response = client.get("/api/docs")
    assert response.status_code == 200
    assert client.head("/api/docs").status_code == 200
    assert response.headers["content-security-policy"] == SECURITY_HEADERS["Content-Security-Policy"]
    assets = Assets()
    assets.feed(response.text)
    assert not assets.inline
    assert assets.urls and all(url.startswith("/static/") for url in assets.urls)
    for url in assets.urls:
        asset = client.get(url)
        assert asset.status_code == 200, url
        assert asset.headers["x-content-type-options"] == "nosniff"
    assert client.get("/api/openapi.json").status_code == 200
