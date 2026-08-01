from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from collections.abc import Sequence
from typing import Any

from .domain import Action, ModelDecision, PolicyDocument, RefundRequest


class OpenRouterError(RuntimeError):
    pass


class OpenRouterDecisionModel:
    endpoint = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(
        self,
        api_key: str,
        model: str = "~openai/gpt-latest",
        *,
        timeout_seconds: float = 30.0,
    ) -> None:
        if not api_key:
            raise ValueError("an OpenRouter API key is required")
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    @classmethod
    def from_environment(
        cls, model: str | None = None, *, timeout_seconds: float = 30.0
    ) -> "OpenRouterDecisionModel":
        api_key = os.environ.get("OPENROUTER_API_KEY", "")
        selected_model = model or os.environ.get(
            "OPENROUTER_MODEL", "~openai/gpt-latest"
        )
        return cls(api_key, selected_model, timeout_seconds=timeout_seconds)

    def decide(
        self, request: RefundRequest, evidence: Sequence[PolicyDocument]
    ) -> ModelDecision:
        body = {
            "model": self.model,
            "temperature": 0,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are the reasoner inside a fail-closed refund workflow. "
                        "Use only the supplied policy documents. Cite document IDs exactly. "
                        "Return escalate when the evidence is insufficient."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "request": request.__dict__,
                            "policies": [document.__dict__ for document in evidence],
                        },
                        sort_keys=True,
                    ),
                },
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "refund_decision",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": [action.value for action in Action],
                            },
                            "citations": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "confidence": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                            },
                            "rationale": {"type": "string", "minLength": 1},
                        },
                        "required": [
                            "action",
                            "citations",
                            "confidence",
                            "rationale",
                        ],
                        "additionalProperties": False,
                    },
                },
            },
        }
        request_object = urllib.request.Request(
            self.endpoint,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "X-OpenRouter-Title": "The Shape of Failure",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(
                request_object, timeout=self.timeout_seconds
            ) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
            raise OpenRouterError("OpenRouter request failed") from error

        try:
            content = payload["choices"][0]["message"]["content"]
            parsed: dict[str, Any] = json.loads(content)
            citations = parsed["citations"]
            if not isinstance(citations, list) or not all(
                isinstance(citation, str) for citation in citations
            ):
                raise TypeError("citations must be a list of strings")
            return ModelDecision(
                action=Action(parsed["action"]),
                citations=tuple(citations),
                confidence=parsed["confidence"],
                rationale=parsed["rationale"],
            )
        except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as error:
            raise OpenRouterError("OpenRouter returned an invalid decision") from error
