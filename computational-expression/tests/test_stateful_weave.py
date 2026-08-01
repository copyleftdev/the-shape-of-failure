from dataclasses import replace

from hypothesis.stateful import RuleBasedStateMachine, invariant, rule

from shape_of_failure.domain import Action, ModelDecision
from shape_of_failure.experiment import baseline_policy, baseline_request
from shape_of_failure.models import ScriptedModel, grounded_decision
from shape_of_failure.workflow import DecisionWeaver


class WorkflowMutationMachine(RuleBasedStateMachine):
    """Generates sequences of faults across data, corpus, and model boundaries."""

    def __init__(self) -> None:
        super().__init__()
        self.request = baseline_request()
        self.policy = baseline_policy()
        self.corpus = (self.policy,)
        self.decision = grounded_decision(self.request, self.corpus)

    @rule()
    def remove_identity(self) -> None:
        self.request = replace(self.request, customer_id="")

    @rule()
    def corrupt_money(self) -> None:
        self.request = replace(self.request, amount_cents=-1)

    @rule()
    def age_the_policy_out(self) -> None:
        self.request = replace(self.request, policy_version=99)

    @rule()
    def contradict_the_corpus(self) -> None:
        conflicting = replace(
            self.policy, doc_id="conflicting-policy", refundable=False
        )
        self.corpus = (self.policy, conflicting)

    @rule()
    def invent_a_citation(self) -> None:
        self.decision = replace(self.decision, citations=("invented-policy",))

    @rule()
    def reverse_the_decision(self) -> None:
        reversed_action = (
            Action.DENY
            if self.decision.action is Action.APPROVE
            else Action.APPROVE
        )
        self.decision = replace(self.decision, action=reversed_action)

    @rule()
    def erase_confidence(self) -> None:
        self.decision = replace(self.decision, confidence=0.0)

    @invariant()
    def acceptance_implies_every_boundary_remains_sound(self) -> None:
        model = ScriptedModel(lambda _request, _evidence: self.decision)
        result = DecisionWeaver(model).run(self.request, self.corpus)
        if result.accepted:
            assert self.request.customer_id
            assert self.request.amount_cents >= 0
            assert self.request.policy_version == self.policy.policy_version
            assert len({item.decision_signature for item in self.corpus}) == 1
            assert set(self.decision.citations) <= {
                item.doc_id for item in self.corpus
            }
            assert self.decision.confidence >= 0.75


TestWorkflowMutationMachine = WorkflowMutationMachine.TestCase
