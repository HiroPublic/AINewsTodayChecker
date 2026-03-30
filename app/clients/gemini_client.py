"""Gemini API client."""

from __future__ import annotations

import logging

import httpx


LOGGER = logging.getLogger(__name__)
GEMINI_GENERATE_CONTENT_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


class GeminiClient:
    """Minimal client for Gemini generateContent calls."""

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash", timeout: float = 90.0) -> None:
        self._api_key = api_key
        self._model = model
        self._timeout = timeout

    def is_configured(self) -> bool:
        """Return whether an API key is available."""

        return bool(self._api_key)

    def evaluate_article(self, system_prompt: str, user_prompt: str) -> str:
        """Request a structured article evaluation from Gemini."""

        payload = {
            "systemInstruction": {
                "parts": [
                    {
                        "text": system_prompt,
                    }
                ]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": user_prompt,
                        }
                    ],
                }
            ],
            "tools": [
                {
                    "google_search": {},
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json",
            },
        }
        url = GEMINI_GENERATE_CONTENT_URL.format(model=self._model)
        LOGGER.info("Requesting article evaluation from Gemini model=%s", self._model)
        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(
                url,
                params={"key": self._api_key},
                json=payload,
            )
            response.raise_for_status()
        data = response.json()
        candidates = data.get("candidates", [])
        if not candidates:
            raise RuntimeError("Gemini returned no candidates")
        parts = candidates[0].get("content", {}).get("parts", [])
        text_parts = [part.get("text", "") for part in parts if part.get("text")]
        if not text_parts:
            raise RuntimeError("Gemini returned no text parts")
        return "\n".join(text_parts)
