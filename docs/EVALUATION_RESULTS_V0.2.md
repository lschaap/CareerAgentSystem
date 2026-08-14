# Career Agent v0.2 baseline evaluation results

## Purpose

This baseline evaluates whether Career Agent produces structured, evidence-aware job-fit
assessments across its three target role families. It establishes a reference point for
future prompt changes; it is not a claim of statistical model accuracy.

## Evaluation details

- Date: August 14, 2026
- Model: `gemini-3.5-flash-lite`
- Dataset: one fictional implementation professional and six fictional jobs
- Expected fit mix: two strong, two borderline, and two poor
- Repetitions: one per case
- Provider responses: six of six completed

The live assessments were validated with the production Pydantic schema and evaluated
with the deterministic checks documented in [the evaluation guide](EVALUATION.md).
Manual review used the guide's 1–5 rubric. Full model responses remain private; only
aggregates and fictional case-level observations are reported here.

## Automated results

| Measure | Result | Rate |
|---|---:|---:|
| Attempted cases | 6 | — |
| Successful provider responses | 6/6 | 100% |
| Schema validation | 6/6 | 100% |
| Score within expected range | 6/6 | 100% |
| Recommendation-category agreement | 2/6 | 33.3% |
| Expected-evidence detection | 6/6 | 100% |
| Expected-gap detection | 6/6 | 100% |
| Preferred-qualification distinction | 5/6 | 83.3% |
| Prohibited-claim absence | 6/6 | 100% |
| All automated checks | 37/42 | 88.1% |

These keyword and phrase checks are regression proxies. They do not prove semantic
correctness, and empty expectations can pass by design. In particular, recommendation
agreement depends on a simple phrase classifier and requires human interpretation.

## Human-review results

| Rubric category | Average (1–5) |
|---|---:|
| Reasoning quality | 3.67 |
| Evidence grounding | 3.50 |
| Tailoring suggestions | 3.17 |
| Interview topics | 1.00 |
| Hallucination control | 3.67 |
| Overall judgment quality | 3.33 |

Definitions for scores 1, 3, and 5 are in the [human-review rubric](EVALUATION.md#human-review-rubric).

## Results by expected fit category

| Expected fit | Cases | Mean fit score | Automated checks | Mean manual rating across rubric |
|---|---:|---:|---:|---:|
| Strong | 2 | 92.5 | 12/14 (85.7%) | 3.33 |
| Borderline | 2 | 71.5 | 11/14 (78.6%) | 3.00 |
| Poor | 2 | 10.0 | 14/14 (100%) | 2.84 |

All six scores landed inside their human-authored ranges. Both poor-fit cases matched the
expected recommendation category. The four strong or borderline cases failed the
automated recommendation-category proxy, and one borderline AI product case did not
clearly distinguish an expected preferred qualification.

## Consistency

Only one assessment was run per case, so repeated-run score consistency was not measured.
A future comparison should use explicitly requested repetitions and report score ranges
without treating small samples as reliability estimates.

## Observed strengths

- Every response conformed to the required schema.
- All scores fell within the expected ranges and clearly separated strong, borderline,
  and poor cases.
- The proxy checks found the expected experience and required gaps in every case.
- No configured prohibited invented claim was detected.
- Manual review rated reasoning and hallucination control strongest, both at 3.67/5.

## Failure patterns and disagreements

- Recommendation wording agreed with the expected automated category in only two cases.
  Because classification is phrase-based, this is evidence for review rather than proof
  that four judgments were semantically wrong.
- Preferred status was unclear for one expected qualification in the borderline AI
  product case.
- Interview topics were the clearest systematic weakness, averaging 1.00/5.
- Tailoring suggestions and overall judgment were useful but moderate rather than strong.

## Hallucination findings

All six prohibited-claim checks passed. Manual hallucination-control ratings averaged
3.67/5, indicating no systematic severe fabrication but leaving room to reduce ambiguity
or overstatement. These checks cover known fictional claims and cannot establish that
every statement was grounded.

## Calibration decision

**Minor prompt calibration needed.** Structural validity, score separation, evidence
recognition, gap detection, and prohibited-claim avoidance were strong. The evidence does
not support a broad rewrite. A future, separately reviewed calibration should narrowly
target useful interview topics, explicit required-versus-preferred wording, and clearer
recommendation language. The production prompt was not changed for this report.

## Limitations

- Six fictional cases are not representative of all candidates or jobs.
- Human expectations and ratings are subjective.
- One run per case cannot measure model consistency.
- Keyword checks can miss synonyms or match language in the wrong context.
- Recommendation phrase classification may understate semantic agreement.
- Schema compliance does not establish factual or decision quality.

## Recommended next step

Design a narrowly scoped prompt-calibration proposal for the three observed weaknesses,
then rerun this unchanged baseline dataset with multiple explicitly approved repetitions.
Compare automated outcomes and blinded human ratings before adopting any prompt change.
