"""Unit tests for the CaptureKit plugin. The network is mocked."""

import io
import json
import urllib.error

import hermes_plugin_capturekit as plugin
import pytest
from hermes_plugin_capturekit import _client


class FakeContext:
    def __init__(self, settings=None):
        self.settings = settings or {}
        self.providers, self.tools = [], {}

    def get_config(self, key, default=None):
        return self.settings.get(key, default)

    def register_web_search_provider(self, provider):
        self.providers.append(provider)

    def register_tool(self, name, toolset, schema, handler, check_fn=None, **kwargs):
        self.tools[name] = {"toolset": toolset, "schema": schema, "handler": handler, "check_fn": check_fn}


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class Calls(list):
    """Records each request and answers it with the payload given to respond()."""

    def __init__(self, monkeypatch):
        super().__init__()
        self.monkeypatch = monkeypatch

    def respond(self, payload):
        def urlopen(request, timeout):
            self.append({"request": request, "timeout": timeout})
            return FakeResponse(json.dumps(payload).encode())

        self.monkeypatch.setattr(_client.urllib.request, "urlopen", urlopen)

    def fail(self, status, body):
        def urlopen(request, timeout):
            self.append({"request": request, "timeout": timeout})
            raise urllib.error.HTTPError(request.full_url, status, "error", {}, io.BytesIO(json.dumps(body).encode()))

        self.monkeypatch.setattr(_client.urllib.request, "urlopen", urlopen)

    def unreachable(self):
        def urlopen(request, timeout):
            raise urllib.error.URLError("down")

        self.monkeypatch.setattr(_client.urllib.request, "urlopen", urlopen)


@pytest.fixture
def calls(monkeypatch):
    return Calls(monkeypatch)


@pytest.fixture
def api_key(monkeypatch):
    monkeypatch.setattr(_client, "get_secret", lambda name, default=None: "test-key" if name == _client.KEY_ENV else default)


@pytest.fixture
def no_key(monkeypatch):
    monkeypatch.setattr(_client, "get_secret", lambda name, default=None: default)


def query(request):
    return dict(_client.urllib.parse.parse_qsl(_client.urllib.parse.urlsplit(request.full_url).query))


def assert_auth(request):
    assert request.get_header("User-agent").startswith("hermes-plugin-capturekit/")
    assert request.get_header("X-api-key") == "test-key"


def provider(settings=None):
    ctx = FakeContext(settings)
    plugin.register(ctx)
    return ctx.providers[0]


RESPONSE = {"success": True, "data": {"metadata": {"title": "Example Domain", "description": "", "favicon": "data:,"},
                                      "markdown": "Example Domain\n\nThis domain is for examples."}}


def test_register_adds_an_extract_only_provider():
    p = provider()
    assert p.name == "capturekit"
    assert p.supports_search() is False
    assert p.supports_extract() is True


def test_not_available_without_key(no_key, calls):
    assert provider().is_available() is False
    [doc] = provider().extract(["https://example.com"])
    assert "CAPTUREKIT_API_KEY" in doc["error"]
    assert calls == []


def test_extract_requests_markdown_of_the_main_content(api_key, calls):
    calls.respond(RESPONSE)
    provider().extract(["https://example.com"])
    request = calls[0]["request"]
    assert request.full_url.startswith("https://api.capturekit.dev/v1/content?")
    assert query(request) == {"url": "https://example.com", "include_markdown": "true", "remove_cookie_banners": "true", "use_defuddle": "true"}
    assert_auth(request)


def test_full_page_when_main_content_only_is_off(api_key, calls):
    calls.respond(RESPONSE)
    provider({"main_content_only": False}).extract(["https://example.com"])
    assert "use_defuddle" not in query(calls[0]["request"])


def test_extract_maps_the_document(api_key, calls):
    calls.respond(RESPONSE)
    [doc] = provider().extract(["https://example.com"])
    assert doc == {
        "url": "https://example.com",
        "title": "Example Domain",
        "content": "Example Domain\n\nThis domain is for examples.",
        "raw_content": "Example Domain\n\nThis domain is for examples.",
        "metadata": {"source": "capturekit", "title": "Example Domain", "description": ""},
    }


def test_one_document_per_url_and_per_url_errors(api_key, calls):
    calls.respond(RESPONSE)
    docs = provider().extract(["https://example.com", "ftp://example.com"])
    assert [d["url"] for d in docs] == ["https://example.com", "ftp://example.com"]
    assert "error" not in docs[0] and "http" in docs[1]["error"]
    assert len(calls) == 1


def test_api_error_message_is_returned(api_key, calls):
    calls.fail(402, {"error": "Not enough credits"})
    [doc] = provider().extract(["https://example.com"])
    assert doc["error"] == "CaptureKit: Not enough credits"


def test_network_error(api_key, calls):
    calls.unreachable()
    [doc] = provider().extract(["https://example.com"])
    assert doc["error"] == "CaptureKit: could not reach the API"


def test_unexpected_response(api_key, calls):
    calls.respond({"success": True, "data": {}})
    [doc] = provider().extract(["https://example.com"])
    assert "markdown" in doc["error"]
