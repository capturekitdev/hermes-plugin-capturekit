"""CaptureKit web extract backend for Hermes Agent."""


def register(ctx):
    from .provider import CaptureKitWebExtractProvider

    ctx.register_web_search_provider(CaptureKitWebExtractProvider(ctx))
