import json

import pytest

from shape_of_failure.domain import Action
from shape_of_failure.experiment import baseline_policy, baseline_request
from shape_of_failure.openrouter import OpenRouterDecisionModel, OpenRouterError


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode()


def test_openrouter_boundary_requests_structured_output(monkeypatch) -> None:
    captured = {}
    model_payload = {
        "action": "approve",
        "citations": [baseline_policy().doc_id],
        "confidence": 0.9,
        "rationale": "The policy permits it.",
    }

    def fake_urlopen(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return FakeResponse(
            {"choices": [{"message": {"content": json.dumps(model_payload)}}]}
        )

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    model = OpenRouterDecisionModel("not-a-real-key", "test/model")

    decision = model.decide(baseline_request(), (baseline_policy(),))

    sent = json.loads(captured["request"].data)
    assert sent["response_format"]["type"] == "json_schema"
    assert sent["response_format"]["json_schema"]["strict"] is True
    assert sent["model"] == "test/model"
    assert decision.action is Action.APPROVE
    assert decision.citations == (baseline_policy().doc_id,)


@pytest.mark.parametrize(
    "content",
    [
        "not json",
        json.dumps({"action": "approve"}),
        json.dumps(
            {
                "action": "invented",
                "citations": [],
                "confidence": 1,
                "rationale": "x",
            }
        ),
        json.dumps(
            {
                "action": "approve",
                "citations": "not-a-list",
                "confidence": 1,
                "rationale": "x",
            }
        ),
    ],
)
def test_openrouter_boundary_rejects_malformed_decisions(monkeypatch, content) -> None:
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda *_args, **_kwargs: FakeResponse(
            {"choices": [{"message": {"content": content}}]}
        ),
    )
    model = OpenRouterDecisionModel("not-a-real-key", "test/model")

    with pytest.raises(OpenRouterError):
        model.decide(baseline_request(), (baseline_policy(),))
