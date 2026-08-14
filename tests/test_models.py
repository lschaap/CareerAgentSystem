import pytest
from pydantic import ValidationError

from career_agent.models import Assessment


def test_assessment_rejects_out_of_range_score(assessment: Assessment) -> None:
    payload = assessment.model_dump()
    payload["fit_score"] = 101
    with pytest.raises(ValidationError):
        Assessment.model_validate(payload)


def test_assessment_rejects_unexpected_fields(assessment: Assessment) -> None:
    payload = assessment.model_dump()
    payload["invented_field"] = "not allowed"
    with pytest.raises(ValidationError):
        Assessment.model_validate(payload)
