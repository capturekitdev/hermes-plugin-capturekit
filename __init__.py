"""CaptureKit for Hermes Agent: a web_extract backend plus tools for page content, screenshots and AI page analysis."""


def register(ctx):
    from . import _client
    from .provider import CaptureKitWebExtractProvider
    from .schemas import TOOLS
    from .tools import handler

    ctx.register_web_search_provider(CaptureKitWebExtractProvider(ctx))

    def available():
        return bool(_client.api_key())

    for name, (description, parameters, *_rest) in TOOLS.items():
        ctx.register_tool(
            name=name,
            toolset="capturekit",
            schema={"name": name, "description": description, "parameters": parameters},
            handler=handler(name),
            check_fn=available,
        )
