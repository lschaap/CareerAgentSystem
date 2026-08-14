"""Small Gemini boundary; the rest of the app is provider-independent."""

from google import genai
from google.genai import errors, types
from pydantic import ValidationError

from career_agent.models import Assessment


class AIProviderError(RuntimeError):
    """User-facing AI provider failure with the original exception chained."""


SYSTEM_PROMPT = """You assess a candidate's fit for AI/software implementation,
solutions or technical consulting, and AI product roles. Base every conclusion on
specific evidence in the resume and job description. Distinguish required from
preferred qualifications. Recognize transferable experience. Never invent candidate
experience, credentials, employers, or achievements. Explain important gaps without
automatically disqualifying the candidate. The recommendation is a reasoned judgment,
not a rigid fit-score threshold. Use concise strings. If title or company is absent,
use 'Unknown'. Return only output matching the provided schema."""


def build_prompt(resume_text: str, job_description: str) -> str:
    return f"""{SYSTEM_PROMPT}

<resume>
{resume_text}
</resume>

<job_description>
{job_description}
</job_description>
"""


def analyze_with_gemini(
    resume_text: str,
    job_description: str,
    api_key: str | None,
    model: str,
) -> Assessment:
    if not api_key:
        raise AIProviderError("GEMINI_API_KEY is missing. Add it to .env and restart the app.")

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model,
            contents=build_prompt(resume_text, job_description),
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_json_schema=Assessment.model_json_schema(),
            ),
        )
        if response.parsed is not None:
            return Assessment.model_validate(response.parsed)
        if not response.text:
            raise AIProviderError("Gemini returned no assessment. Try again later.")
        return Assessment.model_validate_json(response.text)
    except AIProviderError:
        raise
    except ValidationError as exc:
        raise AIProviderError(
            "Gemini returned an incomplete or malformed assessment. Retry the analysis."
        ) from exc
    except errors.APIError as exc:
        status = getattr(exc, "code", None)
        if status == 401:
            message = "Gemini authentication failed. Check GEMINI_API_KEY and restart the app."
        elif status == 403:
            message = (
                "Gemini denied content-generation access for this API key's project. "
                "Check the project status in Google AI Studio or contact Google support."
            )
        elif status == 404:
            message = (
                f"The configured Gemini model '{model}' is unavailable for this account. "
                "Set GEMINI_MODEL to a current free-tier model and restart the app."
            )
        elif status == 400:
            message = (
                "Gemini rejected the analysis request. Check that GEMINI_MODEL names a "
                "current model with structured-output support."
            )
        elif status == 429:
            message = "Gemini's free-tier rate or quota limit was reached. Wait and try again."
        else:
            message = "Gemini could not complete the request. Check the network and try again."
        raise AIProviderError(message) from exc
    except (OSError, TimeoutError) as exc:
        raise AIProviderError("A network error interrupted the Gemini request. Try again.") from exc
    except Exception as exc:
        raise AIProviderError(
            "Gemini returned an unexpected response. See technical details."
        ) from exc
