from pathlib import Path

from career_agent.database import AnalysisRepository
from career_agent.models import Assessment


def test_save_and_retrieve(tmp_path: Path, assessment: Assessment) -> None:
    repository = AnalysisRepository(tmp_path / "career.db")
    repository.initialize()
    saved = repository.save(
        job_url="https://example.test/fictional-role",
        job_description="Fictional job description " * 20,
        resume_text="Fictional resume experience " * 20,
        model_used="mock-model",
        assessment=assessment,
    )
    records = repository.list()
    assert len(records) == 1
    assert records[0].id == saved.id
    assert records[0].assessment == assessment
