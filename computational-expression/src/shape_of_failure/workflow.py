from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Protocol, Sequence

from .contract import (
    citations_are_grounded,
    citations_have_valid_shape,
    confidence_is_acceptable,
    corpus_is_consistent,
    is_non_empty_string,
    is_known_action,
    is_non_negative_integer,
    is_positive_integer,
    is_supported_product,
    policy_matches,
    request_is_eligible,
)
from .domain import (
    Action,
    ModelDecision,
    PolicyDocument,
    RefundRequest,
    TraceEvent,
    WorkflowResult,
)


class DecisionModel(Protocol):
    def decide(
        self, request: RefundRequest, evidence: Sequence[PolicyDocument]
    ) -> ModelDecision: ...


class ShapeAgent:
    """Rejects data the organization has not explicitly modeled."""

    supported_products = frozenset({"physical", "digital", "subscription"})

    def inspect(self, request: RefundRequest) -> tuple[str, ...]:
        failures: list[str] = []
        if not is_non_empty_string(request.request_id):
            failures.append("request_id must be a non-empty string")
        if not is_non_empty_string(request.customer_id):
            failures.append("customer_id must be a non-empty string")
        if not is_non_negative_integer(request.amount_cents):
            failures.append("amount_cents must be a non-negative integer")
        if not is_non_negative_integer(request.purchase_days_ago):
            failures.append("purchase_days_ago must be a non-negative integer")
        if not is_supported_product(request.product_type, self.supported_products):
            failures.append("product_type is outside the modeled domain")
        if not is_non_empty_string(request.locale):
            failures.append("locale must be a non-empty string")
        if not is_positive_integer(request.policy_version):
            failures.append("policy_version must be a positive integer")
        if not is_non_empty_string(request.reason):
            failures.append("reason must be a non-empty string")
        return tuple(failures)


class EvidenceAgent:
    """Selects authoritative evidence and refuses absent or contradictory corpora."""

    def retrieve(
        self, request: RefundRequest, corpus: Sequence[PolicyDocument]
    ) -> tuple[tuple[PolicyDocument, ...], str | None]:
        matches = tuple(
            document
            for document in corpus
            if policy_matches(request, document)
        )
        if not matches:
            return (), "no policy covers the request's data shape"

        if not corpus_is_consistent(matches):
            return matches, "the authoritative corpus contradicts itself"

        if any(not is_non_empty_string(document.doc_id) for document in matches):
            return matches, "a policy document has no stable identity"
        return matches, None


class CriticAgent:
    """Checks the model's answer against evidence and a computable oracle."""

    minimum_confidence = 0.75

    def review(
        self,
        request: RefundRequest,
        evidence: Sequence[PolicyDocument],
        decision: ModelDecision,
    ) -> str | None:
        if not isinstance(decision, ModelDecision):
            return "the model returned an unknown output shape"
        if not is_known_action(decision.action):
            return "the model returned an unknown action"
        if not citations_have_valid_shape(decision.citations):
            return "the model returned malformed citations"
        if not decision.citations:
            return "the model supplied no citations"
        if not citations_are_grounded(decision.citations, evidence):
            return "the model cited evidence that retrieval did not supply"
        if type(decision.confidence) not in (int, float):
            return "confidence is not numeric"
        if not math.isfinite(decision.confidence) or not 0 <= decision.confidence <= 1:
            return "confidence is outside the modeled range"
        if not confidence_is_acceptable(
            decision.confidence, self.minimum_confidence
        ):
            return "confidence is below the acceptance threshold"
        if not isinstance(decision.rationale, str) or not decision.rationale.strip():
            return "the model supplied no rationale"
        if decision.action is Action.ESCALATE:
            return "the model abstained"

        policy = evidence[0]
        eligible = request_is_eligible(request, policy)
        expected = Action.APPROVE if eligible else Action.DENY
        if decision.action is not expected:
            return "the model decision contradicts the policy oracle"
        return None


@dataclass
class DecisionWeaver:
    """Weaves specialized agents into an observable, fail-closed workflow."""

    model: DecisionModel
    shape_agent: ShapeAgent = ShapeAgent()
    evidence_agent: EvidenceAgent = EvidenceAgent()
    critic_agent: CriticAgent = CriticAgent()

    def run(
        self, request: RefundRequest, corpus: Sequence[PolicyDocument]
    ) -> WorkflowResult:
        trace: list[TraceEvent] = []

        shape_failures = self.shape_agent.inspect(request)
        if shape_failures:
            detail = "; ".join(shape_failures)
            trace.append(TraceEvent("shape", "escalated", detail))
            return WorkflowResult(Action.ESCALATE, False, detail, tuple(trace))
        trace.append(TraceEvent("shape", "accepted", "input contract satisfied"))

        evidence, evidence_failure = self.evidence_agent.retrieve(request, corpus)
        if evidence_failure:
            trace.append(TraceEvent("evidence", "escalated", evidence_failure))
            return WorkflowResult(
                Action.ESCALATE, False, evidence_failure, tuple(trace)
            )
        trace.append(
            TraceEvent(
                "evidence", "accepted", f"retrieved {len(evidence)} policy document(s)"
            )
        )

        try:
            decision = self.model.decide(request, evidence)
        except Exception as error:
            detail = f"model boundary failed: {type(error).__name__}"
            trace.append(TraceEvent("model", "escalated", detail))
            return WorkflowResult(Action.ESCALATE, False, detail, tuple(trace))
        criticism = self.critic_agent.review(request, evidence, decision)
        action_detail = (
            decision.action.value
            if isinstance(decision, ModelDecision) and is_known_action(decision.action)
            else "malformed output"
        )
        trace.append(TraceEvent("model", "answered", action_detail))
        if criticism:
            trace.append(TraceEvent("critic", "escalated", criticism))
            return WorkflowResult(
                Action.ESCALATE, False, criticism, tuple(trace), decision
            )

        trace.append(TraceEvent("critic", "accepted", "decision satisfies contract"))
        return WorkflowResult(
            decision.action,
            True,
            "decision accepted",
            tuple(trace),
            decision,
        )
