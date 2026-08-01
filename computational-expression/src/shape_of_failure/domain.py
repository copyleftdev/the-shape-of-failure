from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Action(str, Enum):
    APPROVE = "approve"
    DENY = "deny"
    ESCALATE = "escalate"


@dataclass(frozen=True)
class RefundRequest:
    request_id: str
    customer_id: str
    amount_cents: int
    purchase_days_ago: int
    product_type: str
    locale: str
    policy_version: int
    reason: str


@dataclass(frozen=True)
class PolicyDocument:
    doc_id: str
    locale: str
    product_type: str
    policy_version: int
    max_days: int
    max_amount_cents: int
    refundable: bool

    @property
    def decision_signature(self) -> tuple[bool, int, int]:
        return (self.refundable, self.max_days, self.max_amount_cents)


@dataclass(frozen=True)
class ModelDecision:
    action: Action
    citations: tuple[str, ...]
    confidence: float
    rationale: str


@dataclass(frozen=True)
class TraceEvent:
    agent: str
    state: str
    detail: str


@dataclass(frozen=True)
class WorkflowResult:
    action: Action
    accepted: bool
    reason: str
    trace: tuple[TraceEvent, ...]
    model_decision: ModelDecision | None = None
