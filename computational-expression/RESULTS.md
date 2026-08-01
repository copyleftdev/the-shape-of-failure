# Verification record

Verified on 2026-08-01 with Python 3.13.7:

- Hypothesis 6.164.0
- Pytest 9.1.1
- Mutmut 3.7.0
- 80 tests passed
- 43 of 43 generated mutations to the safety-contract kernel were killed
- The deterministic demo accepted its clean control and detected all seven
  injected data, evidence, and model faults

The first broad mutation run was intentionally instructive: 185 of 374
mutations survived because it included prompt wording, trace text, and gateway
plumbing that the tests did not claim to specify. The mutation boundary was then
made explicit: Mutmut copies the full package but scores `contract.py`, the
kernel containing the acceptance predicates. This is the article's thesis in
miniature—define the deliverable before interpreting a score.

The live OpenRouter mode was not exercised because no API key was supplied. Its
request construction, strict structured-output contract, and malformed-response
handling are covered with a local transport double.
