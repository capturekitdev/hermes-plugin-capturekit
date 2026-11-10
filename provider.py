"""Adapt CaptureKit's Content API response to the Hermes web_extract contract."""

from __future__ import annotations

from agent.web_search_provider import WebSearchProvider

from . import _client


def _failed(url, message):
    return {"url": url, "title": "", "content": "", "raw_content": "", "error": f"CaptureKit: {message}"}


def _document(url, body):
    data = body.get("data") if isinstance(body, dict) else None
    if not isinstance(data, dict) or not isinstance(data.get("markdown"), str):
        raise ValueError("response must contain data.markdown")
    metadata = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
    title = metadata.get("title")
    return {
        "url": url,
        "title": title if isinstance(title, str) else "",
        "content": data["markdown"],
        "raw_content": data["markdown"],
        "metadata": {"source": "capturekit", **{k: v for k, v in metadata.items() if isinstance(v, str) and k != "favicon"}},
    }


class CaptureKitWebExtractProvider(WebSearchProvider):
    """Extract only: each URL is rendered and returned as Markdown. Pair it with a search backend for web_search."""

    def __init__(self, ctx):
        self._get_config = ctx.get_config

    @property
    def name(self):
        return "capturekit"

    @property
    def display_name(self):
        return "CaptureKit (page content)"

    def is_available(self):
        return bool(_client.api_key())

    def supports_search(self):
        return False

    def supports_extract(self):
        return True

    def get_setup_schema(self):
        return {
            "name": self.display_name,
            "badge": "paid",
            "tag": "Pages as Markdown. Extract only.",
            "env_vars": [{"key": _client.KEY_ENV, "prompt": "CaptureKit API key", "url": "https://app.capturekit.dev"}],
        }

    def extract(self, urls, **kwargs):
        main_only = self._get_config("main_content_only", True) is not False
        documents = []
        for url in urls or []:
            if not isinstance(url, str) or not url.startswith(("http://", "https://")):
                documents.append(_failed(str(url), "the URL must start with http:// or https://"))
                continue
            params = {"url": url, "include_markdown": "true", "remove_cookie_banners": "true"}
            if main_only:
                params["use_defuddle"] = "true"
            try:
                documents.append(_document(url, _client.get("/v1/content", params)))
            except (ValueError, _client.ApiError) as exc:
                documents.append(_failed(url, str(exc)))
        return documents
