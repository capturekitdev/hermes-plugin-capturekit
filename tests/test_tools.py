"""Unit tests for the CaptureKit tools. The network is mocked."""

import io
import json
import urllib.error
from pathlib import Path

import hermes_plugin_capturekit as plugin
import pytest
from hermes_plugin_capturekit import _client
from hermes_plugin_capturekit.schemas import TOOLS


class FakeContext:
    def __init__(self):
        self.providers, self.tools = [], {}

    def get_config(self, key, default=None):
        return default

    def register_web_search_provider(self, provider):
        self.providers.append(provider)

    def register_tool(self, name, toolset, schema, handler, check_fn=None, **kwargs):
        self.tools[name] = {"toolset": toolset, "schema": schema, "handler": handler, "check_fn": check_fn}


class FakeResponse(io.BytesIO):
    headers = {"Content-Type": "application/json"}

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class Calls(list):
    """Records each request and answers it with the payload given to respond()."""

    def __init__(self, monkeypatch):
        super().__init__()
        self.monkeypatch = monkeypatch

    def respond(self, payload=None, status=None):
        def urlopen(request, timeout):
            self.append(request)
            if status:
                raise urllib.error.HTTPError(request.full_url, status, "error", {}, io.BytesIO(json.dumps(payload).encode()))
            return FakeResponse(json.dumps(payload).encode())

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


def tools():
    ctx = FakeContext()
    plugin.register(ctx)
    return ctx.tools


def run(name, args):
    return json.loads(tools()[name]["handler"](args))


def query(request):
    return dict(_client.urllib.parse.parse_qsl(_client.urllib.parse.urlsplit(request.full_url).query))


def test_register_adds_every_tool_in_one_toolset():
    registered = tools()
    assert set(registered) >= set(TOOLS)
    assert {t["toolset"] for t in registered.values()} == {"capturekit"}
    for name, tool in registered.items():
        assert tool["schema"]["name"] == name
        assert tool["schema"]["parameters"]["type"] == "object"
        assert set(tool["schema"]["parameters"]["required"]) <= set(tool["schema"]["parameters"]["properties"])


def test_manifest_lists_every_tool():
    manifest = (Path(__file__).resolve().parents[1] / "plugin.yaml").read_text()
    listed = {line.strip()[2:] for line in manifest.splitlines() if line.strip().startswith("- capturekit_")}
    assert listed == set(tools())


def test_tools_hidden_without_key(no_key):
    assert all(tool["check_fn"]() is False for tool in tools().values())


def test_every_description_names_what_it_returns():
    for name, (description, *_rest) in TOOLS.items():
        assert len(description) > 40, name


def test_tool_sends_arguments_and_returns_the_api_json(api_key, calls):
    calls.respond({"ok": True})
    result = run('capturekit_analyze', {'url': 'https://example.com', 'custom_prompt': 'Who is it for?'})
    request = calls[0]
    assert request.full_url.startswith(_client.BASE_URL + '/v1/analyze')
    assert request.get_method() == 'GET'
    assert request.get_header("X-api-key") == "test-key"
    assert request.get_header("User-agent").startswith("hermes-plugin-capturekit/")
    assert query(request) == {'url': 'https://example.com', 'custom_prompt': 'Who is it for?'}
    assert result == {"ok": True}


def test_empty_arguments_are_left_out(api_key, calls):
    calls.respond({})
    args = dict({'url': 'https://example.com', 'custom_prompt': 'Who is it for?'})
    optional = [p for p in TOOLS['capturekit_analyze'][1]["properties"] if p not in args]
    args.update({p: "" for p in optional[:2]})
    run('capturekit_analyze', args)
    sent = query(calls[0]) if calls[0].data is None else json.loads(calls[0].data)
    assert not any(value == "" for value in sent.values())


@pytest.mark.parametrize("name", [n for n, t in TOOLS.items() if t[1]["required"]])
def test_required_inputs_are_checked_before_any_request(api_key, calls, name):
    calls.respond({})
    result = run(name, {})
    assert result["error"].startswith("CaptureKit: ") and "is required" in result["error"]
    assert calls == []


def test_api_error_message_goes_back_to_the_model(api_key, calls):
    calls.respond({"error": {"message": "Not enough credits"}}, status=402)
    assert run('capturekit_analyze', {'url': 'https://example.com', 'custom_prompt': 'Who is it for?'}) == {"error": "CaptureKit: Not enough credits"}


def test_unreachable_api(api_key, monkeypatch):
    def urlopen(request, timeout):
        raise urllib.error.URLError("down")

    monkeypatch.setattr(_client.urllib.request, "urlopen", urlopen)
    assert run('capturekit_analyze', {'url': 'https://example.com', 'custom_prompt': 'Who is it for?'}) == {"error": "CaptureKit: could not reach the API"}


def test_without_key_no_request_is_sent(no_key, calls):
    result = run('capturekit_analyze', {'url': 'https://example.com', 'custom_prompt': 'Who is it for?'})
    assert "CAPTUREKIT_API_KEY" in result["error"]
    assert calls == []


def test_page_content_asks_for_markdown_and_main_content(api_key, calls):
    calls.respond({"success": True, "data": {"markdown": "# Title\n\nText", "metadata": {"title": "Title"}, "links": []}})
    result = run("capturekit_page_content", {"url": "https://example.com", "remove_ads": True})
    assert query(calls[0]) == {"url": "https://example.com", "remove_ads": "true", "include_markdown": "true", "use_defuddle": "true"}
    assert result["data"]["markdown"] == "# Title\n\nText"


def test_page_content_can_keep_the_whole_page_and_cuts_long_text(api_key, calls):
    calls.respond({"success": True, "data": {"markdown": "x" * 50, "html": "<p>" + "y" * 50}})
    result = run("capturekit_page_content", {"url": "https://example.com", "main_content_only": False, "include_html": True, "max_characters": 10})
    assert "use_defuddle" not in query(calls[0])
    assert result["data"]["markdown"] == "x" * 10 and result["data"]["markdown_truncated"] is True
    assert result["data"]["html"] == "<p>" + "y" * 7 and result["data"]["html_truncated"] is True


def test_page_content_rejects_a_bad_limit_without_a_request(api_key, calls):
    assert "max_characters" in run("capturekit_page_content", {"url": "https://example.com", "max_characters": 0})["error"]
    assert calls == []


def _binary(monkeypatch, recorded, body, content_type):
    class Binary(FakeResponse):
        headers = {"Content-Type": content_type}

    def urlopen(request, timeout):
        recorded.append(request)
        return Binary(body)

    monkeypatch.setattr(_client.urllib.request, "urlopen", urlopen)


def test_screenshot_is_saved_in_the_hermes_screenshot_cache(api_key, monkeypatch, tmp_path):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    recorded = []
    _binary(monkeypatch, recorded, b"\x89PNG fake", "image/png")
    result = run("capturekit_screenshot", {"url": "https://example.com", "full_page": True, "device": "iphone_14_pro"})
    assert query(recorded[0]) == {"url": "https://example.com", "full_page": "true", "device": "iphone_14_pro"}
    saved = Path(result["path"])
    assert saved.parent == tmp_path / "cache" / "screenshots"
    assert saved.read_bytes() == b"\x89PNG fake" and saved.suffix == ".png"
    assert result["media"] == f"MEDIA:{saved}" and result["bytes"] == 9


def test_screenshot_pdf(api_key, monkeypatch, tmp_path):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    _binary(monkeypatch, [], b"%PDF-1.7", "application/pdf")
    assert run("capturekit_screenshot", {"url": "https://example.com", "format": "pdf"})["path"].endswith(".pdf")


def test_screenshot_json_answer_is_an_error_and_writes_nothing(api_key, monkeypatch, tmp_path):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    _binary(monkeypatch, [], json.dumps({"error": "Page timed out"}).encode(), "application/json")
    assert run("capturekit_screenshot", {"url": "https://example.com"}) == {"error": "CaptureKit: Page timed out"}
    assert not (tmp_path / "cache").exists()


def test_screenshot_api_error(api_key, calls):
    calls.respond({"error": "Invalid URL"}, status=400)
    assert run("capturekit_screenshot", {"url": "https://example.com"}) == {"error": "CaptureKit: Invalid URL"}
