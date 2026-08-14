# Assessment evaluation guide

This harness measures Career Agent assessments across the three v0.1 role families. It
is separate from the Streamlit app and SQLite history. It uses one fictional resume and
six fictional job descriptions: two expected strong fits, two borderline fits, and two
poor fits.

## Automated checks

Each validated assessment is checked for an expected score range, an acceptable
recommendation category, expected evidence, important required gaps, qualifications
explicitly labeled as preferred, and prohibited invented claims.

These deterministic keyword checks are limited proxies, not semantic grading. A failed
check identifies something to inspect; it does not prove the assessment is bad. Passing
checks do not prove that the reasoning is accurate.

## Cost controls and commands

Activate the virtual environment first. A single-case run makes one Gemini call:

```powershell
python -m evaluation.runner --case-id software_implementation_strong
```

An all-case run requires explicit confirmation and makes six calls:

```powershell
python -m evaluation.runner --all --confirm-all
```

Repetitions multiply the call count. This example makes 18 calls:

```powershell
python -m evaluation.runner --all --repetitions 3 --confirm-all
```

The runner prints the planned call count before calling Gemini. An all-case run without
`--confirm-all` exits without making calls. Review current free-tier quotas before a live
run. Automated tests mock the provider and make no Gemini calls.

Detailed JSON and a Markdown summary are written to `data/evaluations/`. This directory
is ignored by Git because reports contain complete model output. Do not publish raw
reports without reviewing them.

## Human-review rubric

Score every category from 1 to 5 and add brief evidence-based notes.

| Category | 1 | 3 | 5 |
|---|---|---|---|
| Reasoning quality | Contradictory or unsupported | Sensible with notable omissions | Nuanced and coherently weighs strengths and gaps |
| Evidence grounding | Mostly unsupported claims | Most important claims trace to source text | Every material conclusion is accurately grounded |
| Tailoring suggestions | Generic or misleading | Some useful role-specific edits | Specific, truthful, high-impact suggestions |
| Interview topics | Irrelevant or generic | Covers several likely areas | Prioritized from the role's strengths and gaps |
| Hallucination control | Serious invented experience | Minor overstatement or ambiguity | No invented facts and uncertainty is explicit |
| Overall quality | Misleading or unusable | Useful with human correction | Decision-support quality with minor caveats |

A person must read the fictional resume, job description, and assessment. Record honest
disagreement with an expected judgment instead of forcing the result into that category.

## Dataset maintenance and limitations

Case configuration is in `evaluation_cases/cases.json`; the resume is
`evaluation_cases/fictional_resume.txt`. Keep content clearly fictional and preserve the
balanced two-strong, two-borderline, two-poor distribution.

- Keyword checks can miss synonyms or match a phrase in the wrong context.
- Recommendation classification uses simple phrases and can be ambiguous.
- Six cases are regression examples, not a representative benchmark.
- Output varies; one run cannot establish reliability.
- Human-authored expected judgments can themselves be wrong.
- Schema validity verifies structure, not truth or decision quality.

The harness does not change the production prompt or schema. If either changes in a
future milestone, rerun tests and complete a fresh human review.
