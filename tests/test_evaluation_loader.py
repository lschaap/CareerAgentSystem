import json

import pytest
from pydantic import ValidationError

from evaluation.loader import dataset_as_dict, find_case, load_dataset
from evaluation.models import EvaluationDataset


def test_public_dataset_loads_with_balanced_cases() -> None:
    dataset, resume_text = load_dataset()

    assert len(dataset.cases) == 6
    assert [case.expected_fit_category for case in dataset.cases].count("strong") == 2
    assert [case.expected_fit_category for case in dataset.cases].count("borderline") == 2
    assert [case.expected_fit_category for case in dataset.cases].count("poor") == 2
    assert "Jordan Rivera" in resume_text
    assert find_case(dataset, "software_implementation_strong").role_family


def test_invalid_case_configuration_is_rejected() -> None:
    raw = dataset_as_dict()
    raw["cases"][0]["acceptable_score_range"] = [90, 20]

    with pytest.raises(ValidationError, match="acceptable_score_range"):
        EvaluationDataset.model_validate_json(json.dumps(raw))


def test_duplicate_case_ids_are_rejected() -> None:
    raw = dataset_as_dict()
    raw["cases"][1]["case_id"] = raw["cases"][0]["case_id"]

    with pytest.raises(ValidationError, match="unique"):
        EvaluationDataset.model_validate(raw)
