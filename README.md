# CaptureKit for Hermes Agent

Read, capture and understand web pages from [Hermes Agent](https://hermes-agent.nousresearch.com), through the [CaptureKit](https://www.capturekit.dev) API.

- **Page content as clean Markdown**, with the page's metadata and links. CaptureKit loads the page in a real browser, so JavaScript sites work too.
- **Screenshots and PDFs** of any page: the visible part, the full page, one element, or the view on a phone or tablet. The file lands on your machine, ready to show or send.
- **AI page analysis**: summary, value proposition, features, audience, use cases and contact details of a website, in one call.
- **A backend for the built-in `web_extract` tool**, so every page Hermes reads comes back as Markdown.

## Contents

- [Install](#install)
- [How it works](#how-it-works)
- [Tools](#tools)
- [Page content](#page-content)
- [Screenshots and PDFs](#screenshots-and-pdfs)
- [AI page analysis](#ai-page-analysis)
- [Use it as the web_extract backend](#use-it-as-the-web_extract-backend)
- [Example prompts](#example-prompts)
- [Credits and errors](#credits-and-errors)
- [What it does on your machine](#what-it-does-on-your-machine)

## Install

```sh
hermes plugins install capturekit
```

Hermes asks for `CAPTUREKIT_API_KEY` during the install. Create a key in the [CaptureKit dashboard](https://app.capturekit.dev).

Answer yes to `Enable 'capturekit' now?`, or run `hermes plugins enable capturekit` later. The tools join the `capturekit` toolset, which is on by default; turn it on or off in `hermes tools` like any other toolset. They stay hidden from the model until the API key is set.

## How it works

Each tool is one HTTPS call to `https://api.capturekit.dev`, authenticated with your key. CaptureKit opens the page in a headless browser on its side, waits for it to load, can remove cookie banners and ads, then returns what you asked for: the content as Markdown and JSON, an image or PDF, or an AI reading of the page.

```
Hermes  ──tool call──▶  plugin  ──GET /v1/...──▶  api.capturekit.dev  ──browser──▶  page
        ◀──JSON / file──       ◀──JSON / image──
```

## Tools

| Tool | What it returns | Input | Credits |
|---|---|---|---|
| `capturekit_page_content` | Load a web page in a real browser and return its content as Markdown, with its metadata (title, description, Open Graph image) and its internal, external and social links. main_content_only keeps the article and drops menus, sidebars and footers. Can also return the raw HTML and the site's sitemap. | `url` | 1 |
| `capturekit_screenshot` | Take a screenshot of a web page (PNG, JPEG, WebP) or save it as a PDF. Full page, a single element (selector), or a phone or tablet view (device). The file is saved on this machine and its path comes back as `MEDIA:<path>`, so it can be shown or sent to the user. | `url` | 1 |
| `capturekit_analyze` | Read a web page with AI and return a summary, the value proposition, key features, categories, use cases, target audience, and the emails and phone numbers found. Add custom_prompt for your own question about the page. | `url` | 1 |
| `capturekit_usage` | Your CaptureKit account: plan, credits used, credits left, renewal date and rate limit. | none | free |

## Page content

`capturekit_page_content` returns:

- `data.markdown`: the page as Markdown;
- `data.metadata`: title, description, Open Graph image and favicon;
- `data.links`: the links found on the page, split into internal, external and social;
- `data.html` and `data.sitemap` when you ask for them with `include_html` or `include_sitemap`.

By default `main_content_only` is on: CaptureKit keeps the article, product or documentation body and drops navigation, sidebars, comments and footers, which saves tokens. Turn it off to get the whole page. Long pages are cut at `max_characters` (20,000 by default), and `markdown_truncated` tells the model when that happened.

For pages that load slowly or behind a click, use `wait_until` (`networkidle0` waits until the network is quiet), `wait_for_selector` (wait for an element such as `.price`) or `delay` (extra seconds). `remove_cookie_banners`, `remove_ads` and `remove_selectors` clean the page before it is read; `block_resources` (for example `image,font,media`) makes it load faster.

## Screenshots and PDFs

`capturekit_screenshot` captures the page and saves the file under Hermes's screenshot cache, `$HERMES_HOME/cache/screenshots/` (by default `~/.hermes/cache/screenshots/`). The result gives the path and a `MEDIA:<path>` tag, so Hermes can show the image in the chat or send it on Telegram, Discord or any connected platform:

```json
{
  "url": "https://example.com",
  "format": "png",
  "bytes": 182344,
  "path": "/home/me/.hermes/cache/screenshots/capturekit_20261112_101500_3f9a1c2b.png",
  "media": "MEDIA:/home/me/.hermes/cache/screenshots/capturekit_20261112_101500_3f9a1c2b.png"
}
```

| What you want | Arguments |
|---|---|
| The visible part of the page | `url` |
| The whole page, top to bottom | `full_page: true`, and `full_page_scroll: true` when images load on scroll |
| One element, such as a chart or pricing table | `selector: ".pricing"` |
| The mobile view | `device`, for example `iphone_14_pro`, `pixel_7_pro`, `galaxy_s23` or `ipad` |
| A PDF of the page | `format: pdf` |
| A smaller file | `format: webp` or `jpeg`, with `image_quality` |
| A sharper image | `scale_factor: 2` |
| A custom window size | `viewport_width`, `viewport_height` |

Hermes's cache cleanup keeps `cache/screenshots`, so delete old captures yourself when you no longer need them.

## AI page analysis

`capturekit_analyze` reads the page with an AI model on CaptureKit's side and returns a structured profile of it: `summary`, `valueProposition`, `keyFeatures`, `categories`, `useCases`, `targetAudience`, and the `emails` and `phoneNumbers` found. Add `custom_prompt` to ask your own question about the page. It is a quick way to qualify a list of company websites or understand a competitor without reading every page.

## Use it as the web_extract backend

Hermes's built-in `web_extract` tool can also read pages through CaptureKit. Select it in `hermes tools`, or in `~/.hermes/config.yaml`:

```yaml
web:
  extract_backend: capturekit
```

| Setting | Default | Meaning |
|---|---|---|
| `main_content_only` | `true` | Keep the main content of each page and drop navigation, footers and sidebars. |

Set it in the plugin's settings form (Plugins tab of the Hermes desktop app), or in `~/.hermes/config.yaml`:

```yaml
plugins:
  entries:
    capturekit:
      settings:
        main_content_only: false
```

The backend is extract only, so keep a search backend for `web_search`. The tools above work with or without this setting.

## Example prompts

- "Read https://docs.python.org/3/whatsnew/3.13.html and list the five biggest changes."
- "Take a full-page screenshot of example.com and send it to me."
- "Show me how stripe.com/pricing looks on an iPhone 14 Pro."
- "Save https://example.com/report as a PDF."
- "Capture only the pricing table of https://example.com/pricing."
- "Analyze these five SaaS websites and tell me who each one is for and what it costs."
- "Get every link on https://example.com/blog and tell me which ones are articles."
- "How many CaptureKit credits do I have left?"

## Credits and errors

- Content, screenshots and analysis use 1 credit per call; `capturekit_usage` is free. The cost is at the end of each tool's description, so the model knows it before it calls. Plans and prices: [capturekit.dev/pricing](https://www.capturekit.dev/pricing).
- `cache: true` lets CaptureKit reuse a recent result for the same page.
- Errors come back to the model as `{"error": "CaptureKit: <message>"}` with the API's own message (invalid key, no credits left, page timed out), so it can fix the input or retry with other wait options.
- Calls time out after 120 seconds.

## What it does on your machine

- **Network:** calls `https://api.capturekit.dev` only, with your `CAPTUREKIT_API_KEY`. Calls use credits on your CaptureKit account.
- **Files:** `capturekit_screenshot` writes one image or PDF per call in `$HERMES_HOME/cache/screenshots/`. No other tool writes files.
- **Credentials:** reads the key only through Hermes's secret scope. It stores nothing.
- **Nothing else:** no processes started, no telemetry, no self-update. Standard library only, no dependencies.

## Development

```sh
python -m pytest
```

The tests mock the network and run without Hermes installed. `schemas.py` is generated from the CaptureKit OpenAPI spec; each entry holds the tool description, its JSON schema, the API route and the credits per call.

## Contact

- Source: https://github.com/capturekitdev/hermes-plugin-capturekit
- CaptureKit: https://www.capturekit.dev
- Issues: https://github.com/capturekitdev/hermes-plugin-capturekit/issues

## License

MIT
