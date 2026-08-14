import json

from career_agent.provider import AIProviderError
from evaluation.checks import summarize_results
from evaluation.loader import find_case, load_dataset
from evaluation.runner import evaluate_cases, main, render_summary_markdown
from tests.test_evaluation_checks import make_assessment


def test_mocked_single_case_evaluation_makes_one_call() -> None:
    dataset, resume_text = load_dataset()
    case = find_case(dataset, "software_implementation_strong")
    calls = []

    def provider(resume: str, job: str, api_key: str | None, model: str):
        calls.append((resume, job, api_key, model))
        return make_assessment()

    results = evaluate_cases([case], resume_text, 1, "fake-key", "mock-model", provider)

    assert len(calls) == 1
    assert len(results) == 1
    assert results[0].assessment is not None


def test_provider_failure_does_not_stop_remaining_cases() -> None:
    dataset, resume_text = load_dataset()
    cases = dataset.cases[:2]
    call_count = 0

    def provider(resume: str, job: str, api_key: str | None, model: str):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise AIProviderError("fictional provider failure")
        return make_assessment()

    results = evaluate_cases(cases, resume_text, 1, "fake-key", "mock-model", provider)

    assert call_count == 2
    assert results[0].provider_error == "fictional provider failure"
    assert results[1].assessment is not None


def test_all_case_run_requires_confirmation_and_makes_no_calls(tmp_path) -> None:
    def forbidden_provider(*args):
        raise AssertionError("provider must not be called")

    result = main(["--all", "--output-dir", str(tmp_path)], forbidden_provider)

    assert result == 2
    assert list(tmp_path.iterdir()) == []


def test_confirmed_all_case_run_uses_mock_and_saves_local_reports(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    monkeypatch.setenv("GEMINI_MODEL", "mock-model")

    result = main(
        ["--all", "--confirm-all", "--output-dir", str(tmp_path)],
        lambda *args: make_assessment(),
    )

    assert result == 0
    detail = next(tmp_path.glob("evaluation-*.json"))
    payload = json.loads(detail.read_text(encoding="utf-8"))
    assert payload["summary"]["total_runs"] == 6


def test_summary_report_includes_score_variation() -> None:
    dataset, resume_text = load_dataset()
    case = find_case(dataset, "software_implementation_strong")
    scores = iter((80, 87))

    results = evaluate_cases(
        [case],
        resume_text,
        2,
        "fake-key",
        "mock-model",
        lambda *args: make_assessment(score=next(scores)),
    )
    report = render_summary_markdown(summarize_results(results), results, "mock-model")

    assert "## Fit-score variation" in report
    assert "| software_implementation_strong | 80 | 87 | 7 |" in report
