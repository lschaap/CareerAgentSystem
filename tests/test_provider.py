from unittest.mock import Mock, patch

import pytest
from google.genai import errors

from career_agent.models import Assessment
from career_agent.provider import AIProviderError, analyze_with_gemini


def test_missing_api_key_does_not_call_gemini() -> None:
    with patch("career_agent.provider.genai.Client") as client:
        with pytest.raises(AIProviderError, match="missing"):
            analyze_with_gemini("resume", "job", None, "mock-model")
        client.assert_not_called()


def test_gemini_call_is_mocked(assessment: Assessment) -> None:
    response = Mock(parsed=assessment, text=None)
    client = Mock()
    client.models.generate_content.return_value = response
    with patch("career_agent.provider.genai.Client", return_value=client):
        result = analyze_with_gemini("resume", "job", "fake-key", "mock-model")
    assert result == assessment
    client.models.generate_content.assert_called_once()
    config = client.models.generate_content.call_args.kwargs["config"]
    assert config.response_schema is None
    assert config.response_json_schema["additionalProperties"] is False


def test_unavailable_model_has_actionable_message() -> None:
    client = Mock()
    client.models.generate_content.side_effect = errors.ClientError(
        404,
        {"error": {"code": 404, "message": "Model unavailable", "status": "NOT_FOUND"}},
    )
    with patch("career_agent.provider.genai.Client", return_value=client):
        with pytest.raises(AIProviderError, match="GEMINI_MODEL") as exc_info:
            analyze_with_gemini("resume", "job", "fake-key", "retired-model")
    assert "retired-model" in str(exc_info.value)


def test_project_access_denial_has_actionable_message() -> None:
    client = Mock()
    client.models.generate_content.side_effect = errors.ClientError(
        403,
        {
            "error": {
                "code": 403,
                "message": "Your project has been denied access.",
                "status": "PERMISSION_DENIED",
            }
        },
    )
    with patch("career_agent.provider.genai.Client", return_value=client):
        with pytest.raises(AIProviderError, match="project") as exc_info:
            analyze_with_gemini("resume", "job", "fake-key", "mock-model")
    assert "Google AI Studio" in str(exc_info.value)
