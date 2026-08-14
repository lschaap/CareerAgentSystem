"""Conservative public web-page extraction for job descriptions."""

import json
import re
from dataclasses import dataclass
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

MIN_JOB_TEXT_LENGTH = 200


class JobExtractionError(ValueError):
    """Raised when a URL or page does not yield usable job text."""


@dataclass(frozen=True)
class ExtractedJob:
    text: str
    source: str


def _validate_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise JobExtractionError("Enter a complete public http:// or https:// URL.")


def _plain_text(value: object) -> str:
    if isinstance(value, str):
        return BeautifulSoup(value, "html.parser").get_text(" ", strip=True)
    if isinstance(value, list):
        return " ".join(_plain_text(item) for item in value)
    return ""


def _walk_json(value: object):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_json(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_json(child)


def extract_jsonld_job(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            payload = json.loads(script.string or script.get_text())
        except (json.JSONDecodeError, TypeError):
            continue
        for item in _walk_json(payload):
            item_type = item.get("@type")
            types = item_type if isinstance(item_type, list) else [item_type]
            if "JobPosting" in types:
                parts = [
                    _plain_text(item.get("title")),
                    _plain_text(item.get("description")),
                    _plain_text(item.get("qualifications")),
                    _plain_text(item.get("responsibilities")),
                    _plain_text(item.get("skills")),
                ]
                text = "\n\n".join(part for part in parts if part)
                return normalize_text(text) or None
    return None


def extract_plain_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for element in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
        element.decompose()
    main = soup.find("main") or soup.find("article") or soup.body or soup
    return normalize_text(main.get_text("\n", strip=True))


def normalize_text(text: str) -> str:
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def ensure_adequate(text: str) -> str:
    cleaned = normalize_text(text)
    if len(cleaned) < MIN_JOB_TEXT_LENGTH or len(cleaned.split()) < 30:
        raise JobExtractionError(
            "The page did not contain enough meaningful job text. Paste the full description below."
        )
    return cleaned


def fetch_job(url: str, timeout: float = 15) -> ExtractedJob:
    _validate_url(url)
    try:
        response = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": "CareerAgentMVP/1.0 (local learning project)"},
        )
        response.raise_for_status()
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "unknown"
        if status in {401, 403, 429}:
            message = (
                "The website blocked or limited automated retrieval. Paste the job description."
            )
        else:
            message = f"The job page returned HTTP {status}. Paste the job description."
        raise JobExtractionError(message) from exc
    except requests.RequestException as exc:
        raise JobExtractionError(
            "The job page could not be reached. Check the URL/network, or paste the description."
        ) from exc

    content_type = response.headers.get("Content-Type", "")
    if "html" not in content_type.lower() and not response.text.lstrip().startswith("<"):
        raise JobExtractionError("The URL did not return an HTML page. Paste the job description.")

    structured = extract_jsonld_job(response.text)
    if structured:
        return ExtractedJob(ensure_adequate(structured), "JobPosting JSON-LD")
    return ExtractedJob(ensure_adequate(extract_plain_html(response.text)), "readable page text")
