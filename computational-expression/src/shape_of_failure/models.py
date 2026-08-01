from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from .domain import Action, ModelDecision, PolicyDocument, RefundRequest


@dataclass
class ScriptedModel:
    """A deterministic seam for testing orchestration without calling a model."""

    script: Callable[[RefundRequest, Sequence[PolicyDocument]], ModelDecision]
    calls: int = 0

    def decide(
        self, request: RefundRequest, evidence: Sequence[PolicyDocument]
    ) -> ModelDecision:
        self.calls += 1
        return self.script(request, evidence)


def grounded_decision(
    request: RefundRequest, evidence: Sequence[PolicyDocument]
) -> ModelDecision:
    policy = evidence[0]
    eligible = (
        policy.refundable
        and request.purchase_days_ago <= policy.max_days
        and request.amount_cents <= policy.max_amount_cents
    )
    action = Action.APPROVE if eligible else Action.DENY
    return ModelDecision(
        action=action,
        citations=(policy.doc_id,),
        confidence=0.95,
        rationale="The structured request satisfies the cited policy constraints.",
    )


def grounded_model() -> ScriptedModel:
    return ScriptedModel(grounded_decision)
