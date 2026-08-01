from dataclasses import replace

import pytest

from shape_of_failure.domain import Action, ModelDecision
from shape_of_failure.experiment import baseline_policy, baseline_request
from shape_of_failure.models import ScriptedModel, grounded_decision, grounded_model
from shape_of_failure.workflow import DecisionWeaver


def test_control_is_accepted() -> None:
    result = DecisionWeaver(grounded_model()).run(
        baseline_request(), (baseline_policy(),)
    )

    assert result.accepted
    assert result.action is Action.APPROVE
    assert [event.agent for event in result.trace] == [
        "shape",
        "evidence",
        "model",
        "critic",
    ]


@pytest.mark.parametrize(
    "field,value",
    [
        ("request_id", ""),
        ("customer_id", ""),
        ("amount_cents", -1),
        ("amount_cents", True),
        ("purchase_days_ago", -1),
        ("product_type", "unknown"),
        ("locale", ""),
        ("policy_version", 0),
        ("reason", ""),
    ],
)
def test_bad_shapes_escalate_before_the_model(field: str, value: object) -> None:
    model = grounded_model()
    request = replace(baseline_request(), **{field: value})

    result = DecisionWeaver(model).run(request, (baseline_policy(),))

    assert not result.accepted
    assert result.action is Action.ESCALATE
    assert model.calls == 0


def test_missing_policy_escalates_before_the_model() -> None:
    model = grounded_model()
    request = replace(baseline_request(), policy_version=99)

    result = DecisionWeaver(model).run(request, (baseline_policy(),))

    assert not result.accepted
    assert "no policy" in result.reason
    assert model.calls == 0


def test_contradictory_corpus_escalates_before_the_model() -> None:
    model = grounded_model()
    policy = baseline_policy()
    contradiction = replace(policy, doc_id="other", max_days=policy.max_days - 1)

    result = DecisionWeaver(model).run(
        baseline_request(), (policy, contradiction)
    )

    assert not result.accepted
    assert "contradicts" in result.reason
    assert model.calls == 0


@pytest.mark.parametrize(
    "mutation,expected_reason",
    [
        ({"citations": ()}, "no citations"),
        ({"citations": ("invented",)}, "did not supply"),
        ({"confidence": -0.1}, "modeled range"),
        ({"confidence": float("nan")}, "modeled range"),
        ({"confidence": 0.5}, "acceptance threshold"),
        ({"rationale": ""}, "no rationale"),
        ({"action": Action.ESCALATE}, "abstained"),
        ({"action": Action.DENY}, "policy oracle"),
    ],
)
def test_model_faults_are_caught(
    mutation: dict[str, object], expected_reason: str
) -> None:
    request = baseline_request()
    policy = baseline_policy()
    decision = replace(grounded_decision(request, (policy,)), **mutation)
    model = ScriptedModel(lambda _request, _evidence: decision)

    result = DecisionWeaver(model).run(request, (policy,))

    assert not result.accepted
    assert result.action is Action.ESCALATE
    assert expected_reason in result.reason
    assert model.calls == 1


def test_model_boundary_failure_is_visible_without_leaking_details() -> None:
    def fail(_request, _evidence):
        raise RuntimeError("secret upstream detail")

    result = DecisionWeaver(ScriptedModel(fail)).run(
        baseline_request(), (baseline_policy(),)
    )

    assert not result.accepted
    assert result.reason == "model boundary failed: RuntimeError"
    assert "secret" not in result.reason


@pytest.mark.parametrize(
    "malformed,reason",
    [
        (object(), "unknown output shape"),
        (
            ModelDecision("approve", ("policy",), 1.0, "x"),
            "unknown action",
        ),
        (
            ModelDecision(Action.APPROVE, "policy", 1.0, "x"),
            "malformed citations",
        ),
    ],
)
def test_model_adapter_contract_violations_fail_closed(
    malformed: object, reason: str
) -> None:
    model = ScriptedModel(lambda _request, _evidence: malformed)

    result = DecisionWeaver(model).run(
        baseline_request(), (baseline_policy(),)
    )

    assert not result.accepted
    assert result.action is Action.ESCALATE
    assert reason in result.reason
