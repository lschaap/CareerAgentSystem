from unittest.mock import patch

from career_agent.config import load_settings


def test_current_free_tier_model_is_the_default() -> None:
    with patch.dict("os.environ", {}, clear=True):
        settings = load_settings()
    assert settings.gemini_model == "gemini-3.5-flash-lite"
