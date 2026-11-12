"""Tool handlers: each one calls the CaptureKit API and returns a JSON string, errors included."""

from __future__ import annotations

import json
import os
import secrets
import time
import urllib.parse
from pathlib import Path

from . import _client
from .schemas import TOOLS


def _arguments(name, args):
    """Split the model's arguments into the request path, query parameters and JSON body."""
    _, schema, route, mapping, fixed, _cost, _group = TOOLS[name]
    method, path = route.split(" ", 1)
    values, path_values = dict(fixed), {}
    for arg, value in (args or {}).items():
        if value is None or value == "" or arg not in mapping:
            continue
        api_name = mapping[arg]
        if "{" + api_name + "}" in path:
            path_values[api_name] = urllib.parse.quote(str(value).strip(), safe="")
        else:
            values[api_name] = value
    for arg in schema.get("required", []):
        if mapping.get(arg) not in values and mapping.get(arg) not in path_values:
            raise ValueError(f"{arg} is required")
    path = path.format(**path_values)
    if method == "GET":
        params = {k: json.dumps(v, separators=(",", ":")) if isinstance(v, (dict, list)) else v for k, v in values.items()}
        return method, path, params, None
    return method, path, None, values


def call(name, args):
    try:
        method, path, params, body = _arguments(name, args)
        return json.dumps(_client.request(method, path, params, body), ensure_ascii=False)
    except (ValueError, KeyError, _client.ApiError) as exc:
        return json.dumps({"error": f"CaptureKit: {exc}"})


def handler(name):
    def run(args, **kwargs):
        if name == CONTENT:
            return page_content(args)
        if name == SCREENSHOT:
            return screenshot(args)
        return call(name, args)

    run.__name__ = name
    return run


CONTENT = "capturekit_page_content"
SCREENSHOT = "capturekit_screenshot"
DEFAULT_MAX_CHARACTERS = 20000
EXTENSIONS = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp", "application/pdf": "pdf"}


def _limit(value):
    limit = DEFAULT_MAX_CHARACTERS if value in (None, "") else int(value)
    if limit < 1:
        raise ValueError("max_characters must be at least 1")
    return limit


def page_content(args):
    """Markdown (and optionally HTML) of a page, cut to max_characters so a large page does not fill the context."""
    args = dict(args or {})
    main_only = args.pop("main_content_only", True) is not False
    try:
        limit = _limit(args.pop("max_characters", None))
        method, path, params, _ = _arguments(CONTENT, args)
        params["include_markdown"] = True
        if main_only:
            params["use_defuddle"] = True
        body = _client.request(method, path, params)
    except (ValueError, TypeError, KeyError, _client.ApiError) as exc:
        return json.dumps({"error": f"CaptureKit: {exc}"})
    data = body.get("data") if isinstance(body, dict) else None
    if isinstance(data, dict):
        for key in ("markdown", "html"):
            if isinstance(data.get(key), str) and len(data[key]) > limit:
                data[key] = data[key][:limit]
                data[f"{key}_truncated"] = True
    return json.dumps(body, ensure_ascii=False)


def _screenshots_dir():
    try:
        from hermes_constants import get_hermes_home

        home = Path(get_hermes_home())
    except ImportError:
        home = Path(os.environ.get("HERMES_HOME") or Path.home() / ".hermes")
    return home / "cache" / "screenshots"


def screenshot(args):
    """Save the screenshot or PDF under Hermes's screenshot cache and return its path."""
    try:
        method, path, params, _ = _arguments(SCREENSHOT, args)
        raw, content_type = _client.send(method, path, params)
    except (ValueError, KeyError, _client.ApiError) as exc:
        return json.dumps({"error": f"CaptureKit: {exc}"})
    content_type = content_type.split(";")[0].strip().lower()
    extension = EXTENSIONS.get(content_type)
    if not extension or not raw:
        message = "the API did not return an image"
        if content_type == "application/json":
            try:
                message = _client._error_message(raw, 200)
            except Exception:
                pass
        return json.dumps({"error": f"CaptureKit: {message}"})
    folder = _screenshots_dir()
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"capturekit_{time.strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(4)}.{extension}"
    target.write_bytes(raw)
    return json.dumps(
        {"url": params.get("url"), "format": extension, "bytes": len(raw), "path": str(target), "media": f"MEDIA:{target}"}
    )
