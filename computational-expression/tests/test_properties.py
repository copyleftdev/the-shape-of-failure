from dataclasses import replace

from hypothesis import given, strategies as st

from shape_of_failure.domain import Action, ModelDecision, PolicyDocument, RefundRequest
from shape_of_failure.models import ScriptedModel, grounded_model
from shape_of_failure.workflow import DecisionWeaver


identifier = st.text(
    alphabet=st.characters(categories=("Ll", "Lu", "Nd")), min_size=1, max_size=20
)


@st.composite
def valid_worlds(draw):
    product = draw(st.sampled_from(("physical", "digital", "subscription")))
    locale = draw(st.sampled_from(("en-US", "en-GB", "fr-FR")))
    version = draw(st.integers(min_value=1, max_value=20))
    max_days = draw(st.integers(min_value=0, max_value=365))
    max_amount = draw(st.integers(min_value=0, max_value=1_000_000))
    amount = draw(st.integers(min_value=0, max_value=1_000_000))
    age = draw(st.integers(min_value=0, max_value=365))
    refundable = draw(st.booleans())
    request = RefundRequest(
        request_id=draw(identifier),
        customer_id=draw(identifier),
        amount_cents=amount,
        purchase_days_ago=age,
        product_type=product,
        locale=locale,
        policy_version=version,
        reason=draw(identifier),
    )
    policy = PolicyDocument(
        doc_id=draw(identifier),
        locale=locale,
        product_type=product,
        policy_version=version,
        max_days=max_days,
        max_amount_cents=max_amount,
        refundable=refundable,
    )
    return request, policy


@given(valid_worlds())
def test_grounded_decisions_survive_the_entire_weave(world) -> None:
    request, policy = world

    result = DecisionWeaver(grounded_model()).run(request, (policy,))

    eligible = (
        policy.refundable
        and request.purchase_days_ago <= policy.max_days
        and request.amount_cents <= policy.max_amount_cents
    )
    assert result.accepted
    assert result.action is (Action.APPROVE if eligible else Action.DENY)


@given(valid_worlds(), st.integers(max_value=-1))
def test_hypothesis_searches_invalid_amounts_without_model_calls(
    world, invalid_amount: int
) -> None:
    request, policy = world
    request = replace(request, amount_cents=invalid_amount)
    model = grounded_model()

    result = DecisionWeaver(model).run(request, (policy,))

    assert not result.accepted
    assert model.calls == 0


@given(valid_worlds(), identifier)
def test_unknown_citations_can_never_be_accepted(world, unknown_id: str) -> None:
    request, policy = world
    if unknown_id == policy.doc_id:
        unknown_id += "-unknown"
    decision = ModelDecision(
        action=Action.APPROVE,
        citations=(unknown_id,),
        confidence=1.0,
        rationale="Plausible but unsupported.",
    )
    model = ScriptedModel(lambda _request, _evidence: decision)

    result = DecisionWeaver(model).run(request, (policy,))

    assert not result.accepted
    assert result.action is Action.ESCALATE


@given(valid_worlds(), st.integers(min_value=1, max_value=365))
def test_any_material_policy_contradiction_stops_the_model(
    world, difference: int
) -> None:
    request, policy = world
    contradiction = replace(
        policy,
        doc_id=policy.doc_id + "-conflict",
        max_days=policy.max_days + difference,
    )
    model = grounded_model()

    result = DecisionWeaver(model).run(request, (policy, contradiction))

    assert not result.accepted
    assert model.calls == 0
