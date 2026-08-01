from __future__ import annotations

import argparse
import json
from dataclasses import asdict, replace

from .domain import Action, ModelDecision, PolicyDocument, RefundRequest
from .models import ScriptedModel, grounded_decision, grounded_model
from .openrouter import OpenRouterDecisionModel
from .workflow import DecisionWeaver


def baseline_request() -> RefundRequest:
    return RefundRequest(
        request_id="refund-1042",
        customer_id="customer-7",
        amount_cents=4_200,
        purchase_days_ago=12,
        product_type="physical",
        locale="en-US",
        policy_version=3,
        reason="Item arrived damaged.",
    )


def baseline_policy() -> PolicyDocument:
    return PolicyDocument(
        doc_id="refund-policy-en-US-v3",
        locale="en-US",
        product_type="physical",
        policy_version=3,
        max_days=30,
        max_amount_cents=50_000,
        refundable=True,
    )


def _fixed(decision: ModelDecision) -> ScriptedModel:
    return ScriptedModel(lambda _request, _evidence: decision)


def run_demonstration() -> tuple[dict[str, object], ...]:
    request = baseline_request()
    policy = baseline_policy()
    grounded = grounded_decision(request, (policy,))
    conflict = replace(policy, doc_id="conflicting-policy", max_days=7)

    cases = (
        ("control", request, (policy,), grounded_model(), False),
        (
            "missing customer identity",
            replace(request, customer_id=""),
            (policy,),
            grounded_model(),
            True,
        ),
        (
            "negative monetary value",
            replace(request, amount_cents=-1),
            (policy,),
            grounded_model(),
            True,
        ),
        (
            "uncollected policy version",
            replace(request, policy_version=99),
            (policy,),
            grounded_model(),
            True,
        ),
        (
            "contradictory corpus",
            request,
            (policy, conflict),
            grounded_model(),
            True,
        ),
        (
            "hallucinated citation",
            request,
            (policy,),
            _fixed(replace(grounded, citations=("invented-policy",))),
            True,
        ),
        (
            "wrong model decision",
            request,
            (policy,),
            _fixed(replace(grounded, action=Action.DENY)),
            True,
        ),
        (
            "low model confidence",
            request,
            (policy,),
            _fixed(replace(grounded, confidence=0.2)),
            True,
        ),
    )

    report: list[dict[str, object]] = []
    for name, case_request, corpus, model, injected_fault in cases:
        result = DecisionWeaver(model).run(case_request, corpus)
        detected = not result.accepted
        passed = detected if injected_fault else result.accepted
        report.append(
            {
                "scenario": name,
                "injected_fault": injected_fault,
                "passed": passed,
                "final_action": result.action.value,
                "reason": result.reason,
                "model_calls": model.calls,
                "trace": [asdict(event) for event in result.trace],
            }
        )
    return tuple(report)


def run_live(model_name: str | None) -> dict[str, object]:
    model = OpenRouterDecisionModel.from_environment(model_name)
    result = DecisionWeaver(model).run(baseline_request(), (baseline_policy(),))
    return {
        "final_action": result.action.value,
        "accepted": result.accepted,
        "reason": result.reason,
        "trace": [asdict(event) for event in result.trace],
        "model_decision": (
            asdict(result.model_decision) if result.model_decision is not None else None
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the computational expression of The Shape of Failure."
    )
    subparsers = parser.add_subparsers(dest="command", required=False)
    subparsers.add_parser("demo", help="run deterministic fault-injection scenarios")
    live_parser = subparsers.add_parser("live", help="run one live OpenRouter decision")
    live_parser.add_argument("--model", help="OpenRouter model slug")
    args = parser.parse_args()

    if args.command == "live":
        print(json.dumps(run_live(args.model), indent=2, default=str))
        return

    report = run_demonstration()
    print(json.dumps(report, indent=2))
    if not all(case["passed"] for case in report):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
