"""Tool schemas (what the model reads) and how each tool maps to the API.

Each entry: (description, JSON schema of the arguments,
"METHOD /path", {argument: API parameter}, fixed parameters, credits per call, README group).
"""

TOOLS = {
    'capturekit_page_content': (
        "Load a web page in a real browser and return its content as Markdown, with its metadata (title, description, Open Graph image) and its internal, external and social links. main_content_only keeps the article and drops menus, sidebars and footers. Can also return the raw HTML and the site's sitemap. Costs 1 credit per call.",
        {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Page URL, starting with http:// or https://."
                },
                "include_html": {
                    "type": "boolean",
                    "description": "Include the raw HTML of the webpage in the response. Default: false."
                },
                "include_sitemap": {
                    "type": "boolean",
                    "description": "Include the sitemap of the website in the response. Default: false."
                },
                "remove_selectors": {
                    "type": "string",
                    "description": "A comma-separated list of elements to hide before capturing (e.g., ads, popups)."
                },
                "remove_cookie_banners": {
                    "type": "boolean",
                    "description": "Automatically remove cookie banners before capturing. Default: false."
                },
                "remove_ads": {
                    "type": "boolean",
                    "description": "Automatically remove ads before capturing. Default: false."
                },
                "block_resources": {
                    "type": "string",
                    "description": "Comma-separated resource types not to load, for example image,font,media. Pages load faster."
                },
                "block_urls": {
                    "type": "string",
                    "description": "Comma-separated list of URL patterns to block (e.g., “analytics,tracking,advertisement”). You can specify URLs, domains, or simple patterns like “.example.com/”."
                },
                "delay": {
                    "type": "number",
                    "description": "Seconds to wait after the page loads before reading it. Default: 0."
                },
                "wait_until": {
                    "type": "string",
                    "enum": [
                        "domcontentloaded",
                        "load",
                        "networkidle0",
                        "networkidle2"
                    ],
                    "description": "When to capture: load, domcontentloaded, networkidle0 (no network requests for 500 ms) or networkidle2 (at most 2 requests)."
                },
                "wait_for_selector": {
                    "type": "string",
                    "description": "CSS selector to wait for before reading the page."
                },
                "cache": {
                    "type": "boolean",
                    "description": "Cache the response. Default: false."
                },
                "main_content_only": {
                    "type": "boolean",
                    "description": "Keep only the main content (article, product, docs) and drop navigation, sidebars and footers. Default: true."
                },
                "max_characters": {
                    "type": "integer",
                    "description": "Longest Markdown or HTML returned (default 20000); the rest is cut off."
                }
            },
            "required": [
                "url"
            ]
        },
        'GET /v1/content',
        {'url': 'url', 'include_html': 'include_html', 'include_sitemap': 'include_sitemap', 'remove_selectors': 'remove_selectors', 'remove_cookie_banners': 'remove_cookie_banners', 'remove_ads': 'remove_ads', 'block_resources': 'block_resources', 'block_urls': 'block_urls', 'delay': 'delay', 'wait_until': 'wait_until', 'wait_for_selector': 'wait_for_selector', 'cache': 'cache'},
        {},
        '1',
        'Pages',
    ),
    'capturekit_screenshot': (
        'Take a screenshot of a web page (PNG, JPEG, WebP) or save it as a PDF. Full page, a single element (selector), or a phone or tablet view (device). The file is saved on this machine and its path comes back as MEDIA:<path>, so it can be shown or sent to the user. Costs 1 credit per call.',
        {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Page URL, starting with http:// or https://."
                },
                "format": {
                    "type": "string",
                    "enum": [
                        "jpeg",
                        "jpg",
                        "pdf",
                        "png",
                        "webp"
                    ],
                    "description": "The output format of the screenshot. Available formats: - webp - jpeg - jpg - png - pdf Default: png."
                },
                "device": {
                    "type": "string",
                    "enum": [
                        "galaxy_fold4",
                        "galaxy_s23",
                        "galaxy_s23_ultra",
                        "galaxy_s8",
                        "huawei_mate_50_pro",
                        "huawei_p60_pro",
                        "ipad",
                        "iphone_12",
                        "iphone_13_mini",
                        "iphone_13_pro_max",
                        "iphone_14_pro",
                        "iphone_14_pro_max",
                        "iphone_x",
                        "pixel_5",
                        "pixel_6a",
                        "pixel_7_pro",
                        "redmi_note_11",
                        "redmi_note_12_pro"
                    ],
                    "description": "The device type to emulate for the screenshot."
                },
                "full_page": {
                    "type": "boolean",
                    "description": "Capture the entire page instead of just the visible viewport. Default: false."
                },
                "full_page_scroll": {
                    "type": "boolean",
                    "description": "Scroll the page to fully load lazy-loaded elements before capturing a full-page screenshot. Default: false."
                },
                "full_page_scroll_duration": {
                    "type": "number",
                    "description": "Time in milliseconds for scrolling before capturing the full page. Default: 400."
                },
                "viewport_width": {
                    "type": "number",
                    "description": "The width of the browser viewport in pixels. Default: 1280."
                },
                "viewport_height": {
                    "type": "number",
                    "description": "The height of the browser viewport in pixels. Default: 1024."
                },
                "scale_factor": {
                    "type": "number",
                    "description": "The scale factor for high-resolution screenshots. Default: 1."
                },
                "image_quality": {
                    "type": "integer",
                    "description": "Image quality from 1 to 100, for jpeg and webp. Default: 80."
                },
                "selector": {
                    "type": "string",
                    "description": "Capture a specific element on the page instead of the full viewport."
                },
                "cache": {
                    "type": "boolean",
                    "description": "Cache the response. Default: false."
                },
                "remove_selectors": {
                    "type": "string",
                    "description": "A comma-separated list of elements to hide before capturing (e.g., ads, popups)."
                },
                "remove_cookie_banners": {
                    "type": "boolean",
                    "description": "Automatically remove cookie banners before capturing. Default: false."
                },
                "remove_ads": {
                    "type": "boolean",
                    "description": "Automatically remove ads before capturing. Default: false."
                },
                "block_resources": {
                    "type": "string",
                    "description": "Comma-separated resource types not to load, for example image,font,media. Pages load faster."
                },
                "block_urls": {
                    "type": "string",
                    "description": "Comma-separated list of URL patterns to block (e.g., “analytics,tracking,advertisement”). You can specify URLs, domains, or simple patterns like “.example.com/”."
                },
                "delay": {
                    "type": "number",
                    "description": "Seconds to wait after the page loads before taking the screenshot. Default: 0."
                },
                "wait_until": {
                    "type": "string",
                    "enum": [
                        "domcontentloaded",
                        "load",
                        "networkidle0",
                        "networkidle2"
                    ],
                    "description": "When to capture: load, domcontentloaded, networkidle0 (no network requests for 500 ms) or networkidle2 (at most 2 requests)."
                },
                "wait_for_selector": {
                    "type": "string",
                    "description": "CSS selector to wait for before taking the screenshot."
                }
            },
            "required": [
                "url"
            ]
        },
        'GET /v1/capture',
        {'url': 'url', 'format': 'format', 'device': 'device', 'full_page': 'full_page', 'full_page_scroll': 'full_page_scroll', 'full_page_scroll_duration': 'full_page_scroll_duration', 'viewport_width': 'viewport_width', 'viewport_height': 'viewport_height', 'scale_factor': 'scale_factor', 'image_quality': 'image_quality', 'selector': 'selector', 'cache': 'cache', 'remove_selectors': 'remove_selectors', 'remove_cookie_banners': 'remove_cookie_banners', 'remove_ads': 'remove_ads', 'block_resources': 'block_resources', 'block_urls': 'block_urls', 'delay': 'delay', 'wait_until': 'wait_until', 'wait_for_selector': 'wait_for_selector'},
        {},
        '1',
        'Pages',
    ),
    'capturekit_analyze': (
        'Read a web page with AI and return a summary, the value proposition, key features, categories, use cases, target audience, and the emails and phone numbers found. Add custom_prompt for your own question about the page. Costs 1 credit per call.',
        {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Page URL, starting with http:// or https://."
                },
                "custom_prompt": {
                    "type": "string",
                    "description": "Add your own instructions to guide the AI’s analysis."
                },
                "cache": {
                    "type": "boolean",
                    "description": "Cache the response. Default: false."
                }
            },
            "required": [
                "url"
            ]
        },
        'GET /v1/analyze',
        {'url': 'url', 'custom_prompt': 'custom_prompt', 'cache': 'cache'},
        {},
        '1',
        'Pages',
    ),
    'capturekit_usage': (
        'Your CaptureKit account: plan, credits used, credits left, renewal date and rate limit. Free.',
        {
            "type": "object",
            "properties": {},
            "required": []
        },
        'GET /v1/usage',
        {},
        {},
        None,
        'Pages',
    ),
}
