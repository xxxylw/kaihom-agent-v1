import json
from typing import Any, Protocol

import httpx
from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.schemas.clarification import ClarificationQuestion, ParsedClarificationAnswer


class DeepSeekError(RuntimeError):
    pass


class DeepSeekHTTPClient(Protocol):
    def post(
        self,
        url: str,
        *,
        headers: dict[str, str],
        json: dict[str, Any],
        timeout: float,
    ) -> httpx.Response:
        ...


class DeepSeekClient:
    def __init__(
        self,
        settings: Settings | None = None,
        http_client: DeepSeekHTTPClient | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.http_client = http_client or httpx.Client()

    def generate_question(self, redacted_context: dict[str, Any]) -> ClarificationQuestion:
        payload = {
            "instruction": (
                "Generate one concise logistics clarification question. "
                "Return JSON with question_id, text, requested_fields, conflicts, round_number."
            ),
            "context": redacted_context,
        }
        data = self._chat_json(payload)
        try:
            return ClarificationQuestion.model_validate(_normalize_question_payload(data))
        except ValidationError as exc:
            raise DeepSeekError(f"DeepSeek question schema validation failed: {exc}") from exc

    def parse_answer(
        self,
        redacted_context: dict[str, Any],
        answer_text: str,
    ) -> ParsedClarificationAnswer:
        payload = {
            "instruction": (
                "Parse the user's logistics clarification answer. "
                "Return JSON with fields, resolved_conflicts, confidence, notes."
            ),
            "context": redacted_context,
            "answer_text": answer_text,
        }
        data = self._chat_json(payload)
        try:
            return ParsedClarificationAnswer.model_validate(data)
        except ValidationError as exc:
            raise DeepSeekError(f"DeepSeek answer schema validation failed: {exc}") from exc

    def _chat_json(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.settings.deepseek_api_key:
            raise DeepSeekError("KAIHOM_DEEPSEEK_API_KEY is not configured")

        last_error: Exception | None = None
        attempts = self.settings.deepseek_max_retries + 1
        for _attempt in range(attempts):
            try:
                response = self.http_client.post(
                    f"{self.settings.deepseek_base_url.rstrip('/')}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.settings.deepseek_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.settings.deepseek_model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You return strict JSON only.",
                            },
                            {
                                "role": "user",
                                "content": json.dumps(payload, ensure_ascii=True),
                            },
                        ],
                        "response_format": {"type": "json_object"},
                        "stream": False,
                    },
                    timeout=self.settings.deepseek_timeout_seconds,
                )
                response.raise_for_status()
                return _extract_json_content(response.json())
            except Exception as exc:  # noqa: BLE001 - convert every transport/parse error.
                last_error = exc
        raise DeepSeekError(f"DeepSeek request failed: {last_error}") from last_error


def _extract_json_content(data: dict[str, Any]) -> dict[str, Any]:
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise DeepSeekError("DeepSeek response did not include message content") from exc

    if isinstance(content, dict):
        return content
    if not isinstance(content, str):
        raise DeepSeekError("DeepSeek message content is not JSON text")
    parsed = json.loads(content)
    if not isinstance(parsed, dict):
        raise DeepSeekError("DeepSeek JSON content must be an object")
    return parsed


def _normalize_question_payload(data: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(data)
    requested_fields = normalized.get("requested_fields")
    if isinstance(requested_fields, list):
        normalized["requested_fields"] = [
            {"field_name": item} if isinstance(item, str) else item
            for item in requested_fields
        ]
    return normalized
