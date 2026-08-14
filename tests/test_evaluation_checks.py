from datetime import UTC, datetime

from career_agent.models import Assessment, EvidenceItem, GapItem
from evaluation.checks import classify_recommendation, run_checks, summarize_results
from evaluation.loader import find_case, load_dataset
from evaluation.models import CheckResult, EvaluationResult


def make_assessment(*, score: int = 86, invented_claim: str = "") -> Assessment:
    return Assessment(
        job_title="Implementation Consultant",
        company_name="Fictional Systems",
        fit_score=score,
        recommendation="Strong fit; apply.",
        recommendation_reasoning=(
            "The candidate has implementation delivery, discovery, API integration, "
            f"stakeholder training, and customer launch experience. {invented_claim}"
        ),
        matched_requirements=[
            EvidenceItem(
                requirement="Implementation delivery and API integration",
                evidence="Led customer implementations and coordinated API integrations.",
                qualification_type="required",
            ),
            EvidenceItem(
                requirement="SaaS experience",
                evidence="Delivered SaaS customer launches.",
                qualification_type="preferred",
            ),
        ],
        missing_requirements=[
            GapItem(
                requirement="Enterprise architecture certification",
                explanation="No architecture certification appears in the resume.",
                qualification_type="required",
            )
        ],
        transferable_strengths=["Discovery workshops and stakeholder communication"],
        resume_tailoring_suggestions=["Quantify implementation outcomes."],
        likely_interview_topics=["API integration delivery"],
        uncertainties_or_missing_information=["Exact portfolio size is unclear."],
    )


def test_score_range_and_expected_concept_checks() -> None:
    dataset, _ = load_dataset()
    case = find_case(dataset, "software_implementation_strong")

    checks = {check.name: check for check in run_checks(case, make_assessment())}

    assert checks["score_range"].passed
    assert checks["expected_evidence"].passed


def test_recommendation_category_classification() -> None:
    assert classify_recommendation("Strongly recommend applying") == "strong_apply"
    assert (
        classify_recommendation("Consider applying with targeted tailoring") == "conditional_apply"
    )
    assert classify_recommendation("Do not prioritize this poor fit") == "do_not_prioritize"


def test_prohibited_invented_claim_is_detected() -> None:
    dataset, _ = load_dataset()
    case = find_case(dataset, "software_implementation_strong")
    prohibited_term = case.prohibited_invented_claims[0].terms[0]

    checks = {
        check.name: check
        for check in run_checks(case, make_assessment(invented_claim=prohibited_term))
    }

    assert not checks["prohibited_claims"].passed


def test_summary_counts_results_and_score_variation() -> None:
    successful = EvaluationResult(
        case_id="case_one",
        repetition=1,
        created_at=datetime.now(UTC),
        model_used="mock-model",
        assessment=make_assessment(score=80),
        checks=[CheckResult(name="example", passed=True, details="ok")],
    )
    repeated = successful.model_copy(
        update={"repetition": 2, "assessment": make_assessment(score=88)}
    )
    failed = EvaluationResult(
        case_id="case_two",
        repetition=1,
        created_at=datetime.now(UTC),
        model_used="mock-model",
        provider_error="mock failure",
        checks=[CheckResult(name="schema_validation", passed=False, details="failed")],
    )

    summary = summarize_results([successful, repeated, failed])

    assert summary["successful_runs"] == 2
    assert summary["failed_runs"] == 1
    assert summary["checks_passed"] == 2
    assert summary["score_variation_by_case"]["case_one"]["range"] == 8
