# CaptureKit for Hermes Agent

Page content as clean Markdown for the built-in web_extract tool, through the CaptureKit Content API.

## Install

```sh
hermes plugins install capturekit
```

Hermes asks for `CAPTUREKIT_API_KEY` during the install. Create a key in the [CaptureKit dashboard](https://app.capturekit.dev).

Then select it in `hermes tools`, or in `~/.hermes/config.yaml`:

```yaml
web:
  extract_backend: capturekit
```

It is extract only, so keep a search backend for `web_search`.

## Settings

| Setting | Default | Meaning |
|---|---|---|
| `main_content_only` | `true` | Keep the main content of each page and drop navigation, footers and sidebars. |

## What it does on your machine

- **Network:** calls `https://api.capturekit.dev` only, with your `CAPTUREKIT_API_KEY`. Calls can use credits on your CaptureKit account ([pricing](https://www.capturekit.dev/pricing)).
- **Credentials:** reads the key only through Hermes's secret scope. It stores nothing.
- **Nothing else:** no files written, no processes started, no telemetry, no self-update. Standard library only, no dependencies.

## Development

```sh
python -m pytest
```

The tests mock the network and run without Hermes installed.

## Contact

- Source: https://github.com/capturekitdev/hermes-plugin-capturekit
- CaptureKit: https://www.capturekit.dev
- Issues: https://github.com/capturekitdev/hermes-plugin-capturekit/issues

## License

MIT
