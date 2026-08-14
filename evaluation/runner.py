"""Command-line runner for live, local Career Agent evaluations."""

import argparse
import json
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv

from career_agent.config import load_settings
from career_agent.models import Assessment
from career_agent.provider import AIProviderError, analyze_with_gemini
from evaluation.checks import run_checks, summarize_results
from evaluation.loader import find_case, load_dataset
from evaluation.models import CheckResult, EvaluationCase, EvaluationResult

Provider = Callable[[str, str, str | None, str], Assessment]
DEFAULT_OUTPUT_DIR = Path("data/evaluations")


def evaluate_cases(
    cases: list[EvaluationCase],
    resume_text: str,
    repetitions: int,
    api_key: str | None,
    model: str,
    provider: Provider = analyze_with_gemini,
) -> list[EvaluationResult]:
    results: list[EvaluationResult] = []
    for case in cases:
        for repetition in range(1, repetitions + 1):
            created_at = datetime.now(UTC)
            try:
                assessment = provider(resume_text, case.job_description, api_key, model)
                results.append(
                    EvaluationResult(
                        case_id=case.case_id,
                        repetition=repetition,
                        created_at=created_at,
                        model_used=model,
                        assessment=assessment,
                        checks=run_checks(case, assessment),
                    )
                )
            except Exception as exc:
                message = (
                    str(exc) if isinstance(exc, AIProviderError) else f"{type(exc).__name__}: {exc}"
                )
                results.append(
                    EvaluationResult(
                        case_id=case.case_id,
                        repetition=repetition,
                        created_at=created_at,
                        model_used=model,
                        provider_error=message,
                        checks=[
                            CheckResult(
                                name="schema_validation",
                                passed=False,
                                details="No validated Assessment was returned.",
                            )
                        ],
                    )
                )
    return results


def save_results(
    results: list[EvaluationResult],
    model: str,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    detail_path = output_dir / f"evaluation-{timestamp}.json"
    summary_path = output_dir / f"evaluation-{timestamp}-summary.md"
    summary = summarize_results(results)
    detail_path.write_text(
        json.dumps(
            {
                "created_at": datetime.now(UTC).isoformat(),
                "model_used": model,
                "summary": summary,
                "results": [result.model_dump(mode="json") for result in results],
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    summary_path.write_text(render_summary_markdown(summary, results, model), encoding="utf-8")
    return detail_path, summary_path


def render_summary_markdown(summary: dict, results: list[EvaluationResult], model: str) -> str:
    lines = [
        "# Career Agent evaluation summary",
        "",
        f"- Model: `{model}`",
        f"- Total runs: {summary['total_runs']}",
        f"- Successful runs: {summary['successful_runs']}",
        f"- Failed runs: {summary['failed_runs']}",
        f"- Automated checks passed: {summary['checks_passed']}/{summary['checks_total']}",
        "",
        "| Case | Repetition | Score | Automated checks | Provider error |",
        "|---|---:|---:|---:|---|",
    ]
    for result in results:
        score = result.assessment.fit_score if result.assessment else "—"
        passed = sum(check.passed for check in result.checks)
        error = result.provider_error or ""
        lines.append(
            f"| {result.case_id} | {result.repetition} | {score} | "
            f"{passed}/{len(result.checks)} | {error} |"
        )
    lines.extend(
        [
            "",
            "## Fit-score variation",
            "",
            "| Case | Minimum | Maximum | Range |",
            "|---|---:|---:|---:|",
        ]
    )
    for case_id, variation in summary["score_variation_by_case"].items():
        lines.append(
            f"| {case_id} | {variation['minimum']} | {variation['maximum']} | "
            f"{variation['range']} |"
        )
    lines.extend(
        [
            "",
            "## Human review required",
            "",
            "Use the rubric in `docs/EVALUATION.md` to score reasoning, evidence grounding, "
            "tailoring suggestions, interview topics, hallucinations, and overall judgment.",
            "Automated keyword checks are limited proxies and are not semantic quality measures.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run fictional Career Agent evaluations.")
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--case-id", help="Run one case by ID.")
    selection.add_argument("--all", action="store_true", help="Run all six cases.")
    parser.add_argument("--repetitions", type=int, default=1, help="Runs per case (default: 1).")
    parser.add_argument(
        "--confirm-all",
        action="store_true",
        help="Required acknowledgement for an all-case live run.",
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser


def main(argv: list[str] | None = None, provider: Provider = analyze_with_gemini) -> int:
    args = build_parser().parse_args(argv)
    if args.repetitions < 1:
        print("Error: --repetitions must be at least 1.", file=sys.stderr)
        return 2

    dataset, resume_text = load_dataset()
    cases = dataset.cases if args.all else [find_case(dataset, args.case_id)]
    call_count = len(cases) * args.repetitions
    print(f"Planned Gemini calls: {call_count}")
    if args.all and not args.confirm_all:
        print(
            "All-case live runs require --confirm-all. No Gemini calls were made.",
            file=sys.stderr,
        )
        return 2

    load_dotenv()
    settings = load_settings()
    results = evaluate_cases(
        cases,
        resume_text,
        args.repetitions,
        settings.gemini_api_key,
        settings.gemini_model,
        provider,
    )
    detail_path, summary_path = save_results(results, settings.gemini_model, args.output_dir)
    summary = summarize_results(results)
    print(
        f"Completed {summary['successful_runs']}/{summary['total_runs']} runs; "
        f"automated checks passed {summary['checks_passed']}/{summary['checks_total']}."
    )
    print(f"Detailed results: {detail_path}")
    print(f"Summary report: {summary_path}")
    return 0 if summary["failed_runs"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
