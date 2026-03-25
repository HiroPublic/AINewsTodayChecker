"""Perplexity API client."""

from __future__ import annotations

import logging

import httpx


LOGGER = logging.getLogger(__name__)
PERPLEXITY_CHAT_COMPLETIONS_URL = "https://api.perplexity.ai/chat/completions"


class PerplexityClient:
    """Minimal client for Perplexity chat completions."""

    def __init__(self, api_key: str, model: str = "sonar", timeout: float = 30.0) -> None:
        self._api_key = api_key
        self._model = model
        self._timeout = timeout

    def is_configured(self) -> bool:
        """Return whether an API key is available."""

        return bool(self._api_key)

    def evaluate_article(self, system_prompt: str, user_prompt: str) -> str:
        """Request a structured article evaluation from Perplexity."""

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
        }
        LOGGER.info("Requesting article evaluation from Perplexity model=%s", self._model)
        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(PERPLEXITY_CHAT_COMPLETIONS_URL, headers=headers, json=payload)
            response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
