from __future__ import annotations

import math
from collections.abc import Collection, Sequence

from .domain import Action, PolicyDocument, RefundRequest


def is_non_empty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def is_non_negative_integer(value: object) -> bool:
    return type(value) is int and value >= 0


def is_positive_integer(value: object) -> bool:
    return type(value) is int and value >= 1


def is_supported_product(value: object, supported: Collection[str]) -> bool:
    return isinstance(value, str) and value in supported


def is_known_action(value: object) -> bool:
    return isinstance(value, Action)


def policy_matches(request: RefundRequest, policy: PolicyDocument) -> bool:
    return (
        policy.locale == request.locale
        and policy.product_type == request.product_type
        and policy.policy_version == request.policy_version
    )


def corpus_is_consistent(evidence: Sequence[PolicyDocument]) -> bool:
    return bool(evidence) and len(
        {document.decision_signature for document in evidence}
    ) == 1


def citations_are_grounded(
    citations: Sequence[str], evidence: Sequence[PolicyDocument]
) -> bool:
    known = {document.doc_id for document in evidence}
    return bool(citations) and set(citations).issubset(known)


def citations_have_valid_shape(value: object) -> bool:
    return isinstance(value, (list, tuple)) and all(
        is_non_empty_string(citation) for citation in value
    )


def confidence_is_acceptable(value: object, minimum: float) -> bool:
    return (
        type(value) in (int, float)
        and math.isfinite(value)
        and minimum <= value <= 1
    )


def request_is_eligible(
    request: RefundRequest, policy: PolicyDocument
) -> bool:
    return (
        policy.refundable
        and request.purchase_days_ago <= policy.max_days
        and request.amount_cents <= policy.max_amount_cents
    )
