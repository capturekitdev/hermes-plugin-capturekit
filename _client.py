"""HTTP client for the CaptureKit API (standard library only)."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

from agent.secret_scope import get_secret

BASE_URL = "https://api.capturekit.dev"
KEY_ENV = "CAPTUREKIT_API_KEY"
USER_AGENT = "hermes-plugin-capturekit/1.1.0"
TIMEOUT_SECONDS = 120


class ApiError(Exception):
    """A failed call, with a message that can go back to the model."""


def api_key():
    return (get_secret(KEY_ENV) or "").strip()


def _error_message(body, status):
    # Errors arrive as {"error": "message"} or {"error": {"code": "...", "message": "..."}}.
    try:
        error = json.loads(body).get("error")
    except (ValueError, AttributeError):
        error = None
    if isinstance(error, dict):
        error = error.get("message")
    return error if isinstance(error, str) and error else f"request returned HTTP {status}"


def _query_value(value):
    return ("true" if value else "false") if isinstance(value, bool) else value


def send(method, path, params=None, body=None):
    """Call an endpoint and return (raw body, content type). Raises ApiError."""
    key = api_key()
    if not key:
        raise ApiError(f"set {KEY_ENV} through hermes tools or the plugin settings")
    query = {k: _query_value(v) for k, v in (params or {}).items() if v is not None and v != ""}
    url = BASE_URL + path + ("?" + urllib.parse.urlencode(query) if query else "")
    headers = {"Accept": "application/json", "User-Agent": USER_AGENT}
    headers["x-api-key"] = key
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as response:
            headers = getattr(response, "headers", None) or {}
            return response.read(), headers.get("Content-Type", "")
    except urllib.error.HTTPError as exc:
        raise ApiError(_error_message(exc.read(), exc.code)) from None
    except (urllib.error.URLError, TimeoutError):
        raise ApiError("could not reach the API") from None


def request(method, path, params=None, body=None):
    """Call an endpoint and return the decoded JSON body. Raises ApiError."""
    raw, _content_type = send(method, path, params, body)
    try:
        return json.loads(raw) if raw else {}
    except ValueError:
        raise ApiError("the API returned a response that is not JSON") from None


def get(path, params=None):
    """GET a JSON endpoint and return the decoded body. Raises ApiError."""
    return request("GET", path, params)
