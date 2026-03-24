"""OpenAI client placeholder for future claim refinement."""


class OpenAIClient:
    """Placeholder client kept intentionally minimal for future use."""

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def is_configured(self) -> bool:
        """Return whether an API key is available."""

        return bool(self.api_key)
