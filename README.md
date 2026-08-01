# The Shape of Failure

![A detailed human brain formed from turbulent cyan and amber particle-fluid currents on a deep navy field](assets/shape-of-failure-cover.png)

An essay and executable reference implementation for a systems-level claim:
before blaming an AI model, verify the data contract, the deliverable, every
workflow boundary, and the tests used to recognize failure.

## Read

- [The original essay](ai-failure-is-a-systems-failure.md)
- [The DEV Community publication draft](devto-the-shape-of-failure.md)
- [The computational expression](computational-expression/README.md)
- [The verification record](computational-expression/RESULTS.md)

## Reproduce

The companion Python project combines:

- Hypothesis-generated data and stateful workflow sequences;
- Mutmut source-code mutation testing of the safety-contract kernel;
- a visible agent weave for shape, evidence, model, and critic boundaries;
- an optional OpenRouter model call behind the same deterministic contract.

```bash
cd computational-expression
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e '.[test]'
pytest
mutmut run
shape-of-failure demo
```

The checked local run passed 80 tests and killed all 43 generated mutations to
the explicitly scoped safety contract. These results measure this system's
sensitivity to those faults; they are not a universal proof of correctness.
