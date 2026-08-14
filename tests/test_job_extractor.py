import pytest

from career_agent.job_extractor import (
    JobExtractionError,
    ensure_adequate,
    extract_jsonld_job,
    extract_plain_html,
)


def test_extracts_jobposting_jsonld() -> None:
    html = """
    <html><script type="application/ld+json">
    {"@context":"https://schema.org","@type":"JobPosting",
     "title":"AI Solutions Consultant",
     "description":"<p>Lead fictional client implementations and configure AI workflows.</p>",
     "qualifications":"Python, discovery, and communication skills are required."}
    </script><body>Navigation noise</body></html>
    """
    text = extract_jsonld_job(html)
    assert text is not None
    assert "AI Solutions Consultant" in text
    assert "Python" in text


def test_plain_html_prefers_main_and_removes_noise() -> None:
    html = """
    <html><body><nav>Menu noise</nav><main><h1>AI Product Analyst</h1>
    <p>Work with fictional users to define requirements and evaluate model behavior.</p>
    <p>Partner with engineering and communicate product tradeoffs.</p></main>
    <footer>Footer noise</footer></body></html>
    """
    text = extract_plain_html(html)
    assert "AI Product Analyst" in text
    assert "Menu noise" not in text
    assert "Footer noise" not in text


def test_inadequate_text_is_rejected() -> None:
    with pytest.raises(JobExtractionError, match="enough meaningful"):
        ensure_adequate("Apply now")
