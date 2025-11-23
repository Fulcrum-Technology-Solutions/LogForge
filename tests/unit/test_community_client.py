from __future__ import annotations

from logforge.community.client import CommunityClient, CommunityClientConfig


class DummyResponse:
    def __init__(self, status_code: int, json_data=None, content=b"", text=""):
        self.status_code = status_code
        self._json = json_data or {}
        self.content = content
        self.text = text or ""

    def json(self):
        return self._json


class DummySession:
    def __init__(self):
        self.requests = []

    def request(self, method, url, **kwargs):
        self.requests.append((method, url, kwargs))
        return DummyResponse(200, {"results": [{"id": "template"}]})

    def get(self, url, **kwargs):
        self.requests.append(("GET", url, kwargs))
        return DummyResponse(200, content=b"archive")


def test_search_templates_calls_api(monkeypatch):
    session = DummySession()
    client = CommunityClient(CommunityClientConfig(base_url="https://community.example"), session)
    results = client.search_templates("windows")
    assert results[0]["id"] == "template"
    method, url, kwargs = session.requests[0]
    assert method == "GET"
    assert "templates/search" in url
    assert kwargs["params"]["query"] == "windows"


def test_download_template_returns_bytes():
    session = DummySession()
    client = CommunityClient(CommunityClientConfig(base_url="https://community.example"), session)
    data = client.download_template("template")
    assert data == b"archive"
