from __future__ import annotations

import httpx
import pytest

from logforge.community.client import CommunityAPIClient, CommunityAPIError


def test_list_templates_success(monkeypatch):
    def handler(request):
        return httpx.Response(200, json={"templates": [{"id": "acme/simple"}]})

    transport = httpx.MockTransport(handler)

    client = CommunityAPIClient("https://community.example.com")

    def _client_stub():
        return httpx.Client(transport=transport, base_url=client.base_url)

    monkeypatch.setattr(client, "_client", _client_stub)

    templates = client.list_templates()
    assert templates[0]["id"] == "acme/simple"


def test_download_template_error(monkeypatch):
    def handler(request):
        return httpx.Response(404, json={"detail": "Not found"})

    transport = httpx.MockTransport(handler)
    client = CommunityAPIClient("https://community.example.com")

    def _client_stub():
        return httpx.Client(transport=transport, base_url=client.base_url)

    monkeypatch.setattr(client, "_client", _client_stub)

    with pytest.raises(CommunityAPIError):
        client.download_template("missing/template")
