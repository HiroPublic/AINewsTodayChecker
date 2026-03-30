"""Gemini client tests."""

from app.clients.gemini_client import GeminiClient


class _FakeResponse:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": '{"overall_score": 80, "overall_verdict": "MOSTLY_TRUE", "needs_attention": false, "overall_summary": "ok", "claims": []}',
                            }
                        ]
                    },
                    "groundingMetadata": {
                        "webSearchQueries": ["test query"],
                    },
                }
            ]
        }


class _FakeHttpxClient:
    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def post(self, url: str, params: dict, json: dict):
        _FakeHttpxClient.last_request = {
            "url": url,
            "params": params,
            "json": json,
        }
        return _FakeResponse()


def test_gemini_client_enables_google_search_grounding(monkeypatch) -> None:
    monkeypatch.setattr("app.clients.gemini_client.httpx.Client", _FakeHttpxClient)

    client = GeminiClient(api_key="test-key", model="gemini-2.5-flash")
    payload = client.evaluate_article(system_prompt="system", user_prompt="user")

    request = _FakeHttpxClient.last_request
    assert client._timeout == 90.0
    assert request["params"] == {"key": "test-key"}
    assert request["json"]["tools"] == [{"google_search": {}}]
    assert request["json"]["generationConfig"]["responseMimeType"] == "application/json"
    assert "overall_score" in payload
