---
title: "The Shape of Failure: Before You Blame the AI"
published: false
description: "AI projects rarely fail at a single point. Here is how data contracts, agent boundaries, property-based testing, and mutation testing reveal where failure actually enters the system."
tags: ai, testing, python, softwaredevelopment
cover_image: https://raw.githubusercontent.com/copyleftdev/the-shape-of-failure/main/assets/shape-of-failure-cover.png
# canonical_url: https://REPLACE_IF_THIS_WAS_PUBLISHED_ELSEWHERE_FIRST
---

<!--
Before publishing:
1. Set canonical_url only if this article appeared elsewhere first.
2. Change published to true only after previewing the Liquid tags.
-->

Every automated system receives a particular shape of the world.

That shape is expressed through records, documents, events, exceptions, and missing values. If the designers have not identified those forms—and the ways they can become malformed—the machine inherits their ignorance and reproduces it at scale.

{% card %}
**The question is not simply whether the AI failed.**

The useful question is whether the human-built system knew what success meant, knew the shape of its data, and knew how to recognize when it was wrong.
{% endcard %}

## Start with the shape of the data

Before selecting a model, draw the workflow as a sequence of data transformations.

- What enters each stage?
- In what form and from what source?
- Which values are valid, absent, duplicated, stale, delayed, or contradictory?
- How will each violation be detected?
- What must the workflow do next?

Each data shape needs a corresponding failure model. An unknown here is not merely uncertainty for the machine; it is a measurement failure in the organization.

The remedy is to collect the missing data or explicitly design for its absence. Otherwise, the system is being asked to operate in a world its designers have not described.

## Stabilize the deliverable

A system cannot be stabilized around a target that continues to move.

The deliverable must be more than an aspiration written in a prompt. It should be expressed as observable conditions and anchored to a representative corpus:

- examples that are acceptable;
- examples that are unacceptable;
- examples that are genuinely ambiguous.

Human reviewers should first demonstrate that they can apply those distinctions consistently. If they cannot agree on what success looks like, the model is not being measured against a specification. It is being measured against human disagreement disguised as one.

## The model is not the system

Only then does it become meaningful to place an AI model inside the workflow.

The model is one transformation among many:

```text
Input
  → validation
  → retrieval
  → normalization
  → model inference
  → output validation
  → policy checks
  → human action
```

Each transition can discard meaning or introduce error. The fluency of the final response makes the model the most conspicuous suspect, but conspicuousness is not causality.

To assign blame intelligently, observe the entire chain and test every boundary where information is received or transformed.

## Mutation testing attacks confidence itself

Conventional tests ask whether software succeeds under conditions its authors anticipated. Mutation testing reverses that pressure.

It deliberately introduces small faults—reversing a condition, moving a boundary, substituting a value, or removing an operation—and asks whether the test suite notices.

- A **killed mutant** caused at least one test to fail.
- A **surviving mutant** changed the program without the tests objecting.

The resulting score is not proof of correctness. It measures how sensitive the tests are to the generated changes.

In the companion implementation, the focused safety-contract run produced:

{% katex %}
\text{observed mutation sensitivity} = \frac{43\ \text{killed}}{43\ \text{generated}} = 1.0
{% endkatex %}

That number has meaning only because the measurement boundary is explicit: the run scores the small kernel containing the workflow's acceptance predicates. It does not pretend that prompt punctuation or CLI wording is part of the safety contract.

{% details Why the first mutation run mattered %}
The first broad run generated 374 mutations across the package. Of those, 185 survived. Many changed prompt text, trace wording, and gateway plumbing that the tests did not claim to specify.

That was not an embarrassing result to conceal. It revealed an unstable definition of the deliverable. The mutation boundary was then narrowed to the safety-critical contract, and tests were strengthened around exact acceptance boundaries. The experiment therefore reenacted the article's argument: a metric becomes meaningful only after humans define what is being measured.
{% enddetails %}

## Carry the same pressure through the AI workflow

The mutation principle should not stop at source code.

Remove an expected field. Corrupt a format. Supply stale or contradictory source material. Interrupt retrieval. Perturb an instruction. Substitute a fluent but incorrect model response.

At every boundary, ask whether the surrounding system detects the disturbance, abstains, falls back, or routes the case to a human.

The reference implementation makes this flow explicit:

```python
shape_failures = shape_agent.inspect(request)
if shape_failures:
    return escalate(shape_failures)

evidence, evidence_failure = evidence_agent.retrieve(request, corpus)
if evidence_failure:
    return escalate(evidence_failure)

decision = model.decide(request, evidence)
criticism = critic_agent.review(request, evidence, decision)
if criticism:
    return escalate(criticism)

return accept(decision)
```

The actual implementation uses four deliberately small agents:

1. A **shape agent** rejects malformed or unmodeled input.
2. An **evidence agent** retrieves the matching corpus and detects contradictions.
3. A **model agent** proposes a structured, cited decision through OpenRouter.
4. A **critic agent** verifies the decision against citations, confidence thresholds, and a computable policy oracle.

The model is useful, but it is never permitted to define its own success criteria.

## What the executable experiment found

The checked local verification produced:

- 80 passing tests;
- 43 of 43 mutations killed in the safety-contract kernel;
- one clean control accepted;
- all seven injected data, corpus, and model faults detected;
- zero model calls when bad input or contradictory evidence made inference unsafe.

[Hypothesis](https://hypothesis.readthedocs.io/en/latest/stateful.html) generates both data and sequences of workflow mutations. [Mutmut](https://mutmut.readthedocs.io/en/latest/) changes the safety-contract source. [OpenRouter](https://openrouter.ai/docs/guides/features/structured-outputs) supplies the optional live model boundary using a strict JSON Schema response.

The OpenRouter call is intentionally optional because it uses an external service and may incur cost. The deterministic safety oracle does not depend on network access, a particular provider, or a favorable model response.

{% cta https://github.com/copyleftdev/the-shape-of-failure/tree/main/computational-expression %}
Run the computational expression and challenge its assumptions
{% endcta %}

## When is it truly an AI failure?

Only after this discipline has been applied does the phrase *AI failure* acquire useful meaning.

If the input was well formed, the deliverable was stable, the supporting components behaved correctly, and the model still violated a known requirement, then the model failed within the conditions established for it.

But if the data was absent, the target disputed, retrieval defective, or safeguards unable to recognize error, the model may merely be the place where an earlier failure became visible. Calling that an AI failure does not improve the system. It interrupts the feedback by which the organization might learn.

A generative model is an engine of learned resemblance. It can produce behavior that looks remarkably like understanding, but resemblance cannot carry responsibility. People choose the objective, define acceptable evidence, engineer the transitions, and decide what happens when uncertainty enters the system.

Before declaring that the AI failed, demonstrate that the system knew what success meant, knew the shape of its world, and knew how to recognize when it was wrong.

If it did not, the failure began long before the model answered.

---

*The complete experiment includes the agent weave, property-based tests, stateful tests, mutation configuration, deterministic fault-injection CLI, verification record, and optional OpenRouter gateway.*
