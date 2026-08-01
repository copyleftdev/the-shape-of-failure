from dataclasses import replace

import pytest

from shape_of_failure.contract import (
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
from shape_of_failure.experiment import baseline_policy, baseline_request
from shape_of_failure.domain import Action


@pytest.mark.parametrize("value", ["x", "  x  "])
def test_non_empty_string_accepts_content(value: str) -> None:
    assert is_non_empty_string(value)


@pytest.mark.parametrize("value", ["", "   ", None, 1])
def test_non_empty_string_rejects_absence(value: object) -> None:
    assert not is_non_empty_string(value)


@pytest.mark.parametrize("value", [0, 1, 10])
def test_non_negative_integer_boundaries(value: int) -> None:
    assert is_non_negative_integer(value)


@pytest.mark.parametrize("value", [-1, True, 1.0, "1"])
def test_non_negative_integer_rejects_other_shapes(value: object) -> None:
    assert not is_non_negative_integer(value)


@pytest.mark.parametrize("value", [1, 2])
def test_positive_integer_boundaries(value: int) -> None:
    assert is_positive_integer(value)


@pytest.mark.parametrize("value", [0, -1, True, 1.0])
def test_positive_integer_rejects_other_shapes(value: object) -> None:
    assert not is_positive_integer(value)


def test_supported_product_requires_both_shape_and_membership() -> None:
    supported = {"physical", "digital"}
    assert is_supported_product("physical", supported)
    assert not is_supported_product("unknown", supported)
    assert not is_supported_product(None, supported)


def test_known_actions_require_the_enum_contract() -> None:
    assert is_known_action(Action.APPROVE)
    assert is_known_action(Action.DENY)
    assert is_known_action(Action.ESCALATE)
    assert not is_known_action("approve")
    assert not is_known_action(None)


@pytest.mark.parametrize(
    "change",
    [
        {"locale": "fr-FR"},
        {"product_type": "digital"},
        {"policy_version": 4},
    ],
)
def test_policy_match_requires_every_dimension(change: dict[str, object]) -> None:
    request = baseline_request()
    policy = baseline_policy()
    assert policy_matches(request, policy)
    assert not policy_matches(request, replace(policy, **change))


def test_corpus_consistency_requires_evidence_and_one_signature() -> None:
    policy = baseline_policy()
    assert not corpus_is_consistent(())
    assert corpus_is_consistent((policy,))
    assert corpus_is_consistent((policy, replace(policy, doc_id="duplicate")))
    assert not corpus_is_consistent(
        (policy, replace(policy, doc_id="conflict", refundable=False))
    )


def test_citations_must_be_present_and_grounded() -> None:
    policy = baseline_policy()
    assert citations_are_grounded((policy.doc_id,), (policy,))
    assert not citations_are_grounded((), (policy,))
    assert not citations_are_grounded(("invented",), (policy,))


@pytest.mark.parametrize("value", [("policy",), ["policy"], ()])
def test_citation_shape_accepts_string_collections(value: object) -> None:
    assert citations_have_valid_shape(value)


@pytest.mark.parametrize("value", ["policy", None, 1, ("",), (1,)])
def test_citation_shape_rejects_unknown_forms(value: object) -> None:
    assert not citations_have_valid_shape(value)


@pytest.mark.parametrize("value", [0.75, 0.8, 1, 1.0])
def test_confidence_accepts_closed_boundaries(value: float) -> None:
    assert confidence_is_acceptable(value, 0.75)


@pytest.mark.parametrize(
    "value", [0.749999, -1, 1.000001, float("nan"), float("inf"), True, "1"]
)
def test_confidence_rejects_values_outside_contract(value: object) -> None:
    assert not confidence_is_acceptable(value, 0.75)


def test_eligibility_uses_closed_policy_boundaries() -> None:
    policy = baseline_policy()
    request = replace(
        baseline_request(),
        purchase_days_ago=policy.max_days,
        amount_cents=policy.max_amount_cents,
    )
    assert request_is_eligible(request, policy)
    assert not request_is_eligible(
        replace(request, purchase_days_ago=policy.max_days + 1), policy
    )
    assert not request_is_eligible(
        replace(request, amount_cents=policy.max_amount_cents + 1), policy
    )
    assert not request_is_eligible(request, replace(policy, refundable=False))
