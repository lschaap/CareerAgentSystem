"""Validated configuration and result models for the evaluation harness."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from career_agent.models import Assessment

FitCategory = Literal["strong", "borderline", "poor"]
RecommendationCategory = Literal["strong_apply", "conditional_apply", "do_not_prioritize"]


class ConceptExpectation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str = Field(min_length=1)
    terms: list[str] = Field(min_length=1)


class EvaluationCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(pattern=r"^[a-z0-9_]+$")
    role_family: str = Field(min_length=1)
    job_description: str = Field(min_length=200)
    expected_fit_category: FitCategory
    acceptable_score_range: tuple[int, int]
    acceptable_recommendation_categories: list[RecommendationCategory] = Field(min_length=1)
    important_experience: list[ConceptExpectation]
    important_required_gaps: list[ConceptExpectation]
    preferred_qualifications: list[ConceptExpectation]
    prohibited_invented_claims: list[ConceptExpectation]
    expected_judgment: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_score_range(self) -> "EvaluationCase":
        low, high = self.acceptable_score_range
        if not 0 <= low <= high <= 100:
            raise ValueError("acceptable_score_range must be ordered within 0-100")
        return self


class EvaluationDataset(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_name: str = Field(min_length=1)
    resume_file: str = Field(min_length=1)
    cases: list[EvaluationCase] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_case_set(self) -> "EvaluationDataset":
        case_ids = [case.case_id for case in self.cases]
        if len(case_ids) != len(set(case_ids)):
            raise ValueError("evaluation case IDs must be unique")
        categories = [case.expected_fit_category for case in self.cases]
        if len(self.cases) != 6 or any(
            categories.count(value) != 2 for value in ("strong", "borderline", "poor")
        ):
            raise ValueError("dataset must contain six cases: two strong, two borderline, two poor")
        return self


class CheckResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    passed: bool
    details: str


class EvaluationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str
    repetition: int = Field(ge=1)
    created_at: datetime
    model_used: str
    assessment: Assessment | None = None
    provider_error: str | None = None
    checks: list[CheckResult]
