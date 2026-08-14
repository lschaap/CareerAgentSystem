"""Load the public fictional evaluation dataset."""

import json
from pathlib import Path

from evaluation.models import EvaluationCase, EvaluationDataset

DEFAULT_DATASET_PATH = Path(__file__).resolve().parent.parent / "evaluation_cases" / "cases.json"


def load_dataset(path: Path = DEFAULT_DATASET_PATH) -> tuple[EvaluationDataset, str]:
    dataset = EvaluationDataset.model_validate_json(path.read_text(encoding="utf-8"))
    resume_path = path.parent / dataset.resume_file
    resume_text = resume_path.read_text(encoding="utf-8").strip()
    if len(resume_text) < 200:
        raise ValueError("fictional evaluation résumé is too short")
    return dataset, resume_text


def find_case(dataset: EvaluationDataset, case_id: str) -> EvaluationCase:
    for case in dataset.cases:
        if case.case_id == case_id:
            return case
    available = ", ".join(case.case_id for case in dataset.cases)
    raise ValueError(f"Unknown case ID '{case_id}'. Available cases: {available}")


def dataset_as_dict(path: Path = DEFAULT_DATASET_PATH) -> dict:
    """Return raw configuration for tests and editing tools."""
    return json.loads(path.read_text(encoding="utf-8"))
