# The Shape of Failure: Computational Expression

This companion project makes the essay's argument executable. It does not ask
whether a language model appears intelligent. It asks whether the surrounding
system can recognize when its own assumptions have been violated.

The example is a refund-policy workflow with a deliberately narrow contract:

```text
Refund request
    → Shape agent      rejects unknown or malformed inputs
    → Evidence agent   retrieves a matching, non-contradictory corpus
    → Model agent      proposes a structured, cited decision
    → Critic agent     checks citations, confidence, and the policy oracle
    → Decision         approve, deny, or fail closed to human escalation
```

The agents are small on purpose. Their weave is visible in the event trace, and
the OpenRouter model sits behind an interface that deterministic tests can
replace. This keeps network behavior out of the safety oracle.

## What the experiment demonstrates

- Data shape is an executable contract, not prose in a planning document.
- Missing and contradictory evidence stop the workflow before a model call.
- Fluent but wrong decisions, invented citations, malformed outputs, and weak
  confidence fail closed.
- Hypothesis generates values and sequences that exceed a hand-written example
  list, then shrinks a failure to a reproducible case.
- Mutmut alters the safety-contract predicates and measures whether the tests
  notice a changed acceptance boundary.
- A live OpenRouter response must cross the same deterministic boundaries as a
  fake response.

This is evidence for the essay's systems claim, not proof that every failure is
a human failure. It establishes a procedure for finding where a failure entered
the loop.

## Run the deterministic demonstration

Python 3.11 or later is required.

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e '.[test]'
shape-of-failure demo
```

The command injects faults at the data, corpus, and model boundaries. It exits
nonzero if the clean control is rejected or any injected fault escapes.

See the checked [verification record](RESULTS.md) for the observed local run,
including the broad first mutation pass and the focused safety-kernel score.

## Let Hypothesis search the space

```bash
pytest
pytest --hypothesis-show-statistics
```

The stateful test lets Hypothesis weave sequences of mutations across several
agents. Its invariant is simple: acceptance implies that every boundary still
satisfies its independent safety conditions.

## Challenge the tests with source-code mutations

```bash
mutmut run
mutmut results
mutmut browse
```

A surviving mutant is not automatically a defect; equivalent and irrelevant
mutants require review. This project deliberately scores the small
`contract.py` safety kernel instead of prompts, trace wording, or CLI plumbing.
A killed mutant demonstrates that at least one test can observe the behavioral
change. The score measures sensitivity to generated faults, not correctness
itself.

## Run one live OpenRouter decision

Live mode is deliberately opt-in because it uses an external service and may
incur cost. Keep the key in the environment, never in source code:

```bash
export OPENROUTER_API_KEY='your-key'
export OPENROUTER_MODEL='a-model-that-supports-structured-output'
shape-of-failure live
```

The gateway calls OpenRouter's Chat Completions endpoint and requests a strict
JSON Schema response. The returned decision is still treated as untrusted input
by the critic agent.

## Read the proof in this order

1. `src/shape_of_failure/workflow.py` — the observable agent weave.
2. `tests/test_properties.py` — generated data-shape properties.
3. `tests/test_stateful_weave.py` — generated sequences of cross-boundary faults.
4. `tests/test_workflow.py` — explicit controls and known failure modes.
5. `src/shape_of_failure/openrouter.py` — the optional live model boundary.

The implementation follows the current [Hypothesis stateful-testing
model](https://hypothesis.readthedocs.io/en/latest/stateful.html), [OpenRouter
Chat Completions API](https://openrouter.ai/docs/quickstart), [OpenRouter
structured-output format](https://openrouter.ai/docs/guides/features/structured-outputs),
and [Mutmut workflow](https://mutmut.readthedocs.io/en/latest/).
