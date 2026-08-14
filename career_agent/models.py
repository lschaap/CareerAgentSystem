"""Validated domain models used by the UI, AI provider, and database."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class EvidenceItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement: str = Field(min_length=1)
    evidence: str = Field(min_length=1)
    qualification_type: Literal["required", "preferred", "unclear"]


class GapItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement: str = Field(min_length=1)
    qualification_type: Literal["required", "preferred", "unclear"]
    explanation: str = Field(min_length=1)


class Assessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_title: str = Field(min_length=1)
    company_name: str = Field(min_length=1)
    fit_score: int = Field(ge=0, le=100)
    recommendation: str = Field(min_length=1)
    recommendation_reasoning: str = Field(min_length=1)
    matched_requirements: list[EvidenceItem]
    missing_requirements: list[GapItem]
    transferable_strengths: list[str]
    resume_tailoring_suggestions: list[str]
    likely_interview_topics: list[str]
    uncertainties_or_missing_information: list[str]


class AnalysisRecord(BaseModel):
    id: str
    created_at: datetime
    job_url: str
    job_title: str
    company_name: str
    job_description: str
    resume_text: str
    model_used: str
    assessment: Assessment
