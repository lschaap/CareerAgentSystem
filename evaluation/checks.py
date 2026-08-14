"""Deterministic proxy checks for structured Career Agent assessments."""

import json
import re
from collections.abc import Iterable

from career_agent.models import Assessment
from evaluation.models import CheckResult, ConceptExpectation, EvaluationCase


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def concept_present(text: str, concept: ConceptExpectation) -> bool:
    normalized = normalize(text)
    return any(normalize(term) in normalized for term in concept.terms)


def _concept_check(name: str, concepts: Iterable[ConceptExpectation], text: str) -> CheckResult:
    missing = [concept.label for concept in concepts if not concept_present(text, concept)]
    return CheckResult(
        name=name,
        passed=not missing,
        details="All expected concepts were found."
        if not missing
        else f"Missing: {', '.join(missing)}",
    )


def classify_recommendation(text: str) -> str:
    normalized = normalize(text)
    poor_terms = (
        "do not",
        "not recommend",
        "poor fit",
        "not a fit",
        "weak fit",
        "do not prioritize",
    )
    conditional_terms = (
        "apply with",
        "consider applying",
        "conditional",
        "moderate fit",
        "borderline",
        "targeted tailoring",
    )
    strong_terms = (
        "strongly recommend",
        "highly recommend",
        "excellent fit",
        "strong fit",
        "apply",
    )
    if any(term in normalized for term in poor_terms):
        return "do_not_prioritize"
    if any(term in normalized for term in conditional_terms):
        return "conditional_apply"
    if any(term in normalized for term in strong_terms):
        return "strong_apply"
    return "unclassified"


def run_checks(case: EvaluationCase, assessment: Assessment) -> list[CheckResult]:
    low, high = case.acceptable_score_range
    recommendation_category = classify_recommendation(assessment.recommendation)
    evidence_text = " ".join(
        [
            *(f"{item.requirement} {item.evidence}" for item in assessment.matched_requirements),
            *assessment.transferable_strengths,
            assessment.recommendation_reasoning,
        ]
    )
    gap_text = " ".join(
        f"{item.requirement} {item.explanation}"
        for item in assessment.missing_requirements
        if item.qualification_type == "required"
    )
    preferred_text = " ".join(
        f"{item.requirement} {getattr(item, 'evidence', '')} {getattr(item, 'explanation', '')}"
        for item in [*assessment.matched_requirements, *assessment.missing_requirements]
        if item.qualification_type == "preferred"
    )
    complete_text = json.dumps(assessment.model_dump(), ensure_ascii=False)
    invented = [
        concept.label
        for concept in case.prohibited_invented_claims
        if concept_present(complete_text, concept)
    ]

    return [
        CheckResult(name="schema_validation", passed=True, details="Provider returned Assessment."),
        CheckResult(
            name="score_range",
            passed=low <= assessment.fit_score <= high,
            details=f"Score {assessment.fit_score}; expected {low}-{high}.",
        ),
        CheckResult(
            name="recommendation_category",
            passed=recommendation_category in case.acceptable_recommendation_categories,
            details=(
                f"Classified as {recommendation_category}; expected one of "
                f"{', '.join(case.acceptable_recommendation_categories)}."
            ),
        ),
        _concept_check("expected_evidence", case.important_experience, evidence_text),
        _concept_check("expected_required_gaps", case.important_required_gaps, gap_text),
        _concept_check("preferred_distinction", case.preferred_qualifications, preferred_text),
        CheckResult(
            name="prohibited_claims",
            passed=not invented,
            details="No prohibited claims found."
            if not invented
            else f"Found: {', '.join(invented)}",
        ),
    ]


def summarize_results(results: list) -> dict:
    successful = [result for result in results if result.assessment is not None]
    failed = [result for result in results if result.provider_error is not None]
    checks = [check for result in successful for check in result.checks]
    score_variation: dict[str, dict[str, int]] = {}
    for case_id in sorted({result.case_id for result in successful}):
        scores = [
            result.assessment.fit_score
            for result in successful
            if result.case_id == case_id and result.assessment is not None
        ]
        score_variation[case_id] = {
            "minimum": min(scores),
            "maximum": max(scores),
            "range": max(scores) - min(scores),
        }
    return {
        "total_runs": len(results),
        "successful_runs": len(successful),
        "failed_runs": len(failed),
        "checks_passed": sum(check.passed for check in checks),
        "checks_total": len(checks),
        "score_variation_by_case": score_variation,
    }
