import pytest

from career_agent.models import Assessment


@pytest.fixture
def assessment() -> Assessment:
    return Assessment.model_validate(
        {
            "job_title": "AI Implementation Specialist",
            "company_name": "Fictional Systems",
            "fit_score": 78,
            "recommendation": "Apply with targeted tailoring",
            "recommendation_reasoning": "The candidate has relevant delivery experience.",
            "matched_requirements": [
                {
                    "requirement": "Python",
                    "evidence": "Built a fictional Python workflow.",
                    "qualification_type": "required",
                }
            ],
            "missing_requirements": [
                {
                    "requirement": "Cloud certification",
                    "qualification_type": "preferred",
                    "explanation": "No certification is listed.",
                }
            ],
            "transferable_strengths": ["Stakeholder communication"],
            "resume_tailoring_suggestions": ["Make implementation outcomes more prominent."],
            "likely_interview_topics": ["Technical discovery"],
            "uncertainties_or_missing_information": ["Scale of deployments is unclear."],
        }
    )
