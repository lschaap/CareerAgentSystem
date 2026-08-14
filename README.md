# Career Agent MVP

Career Agent MVP is a local-first portfolio project that compares a PDF résumé with a
single job posting. It extracts public job-page content, asks Google Gemini for a
strictly structured assessment, displays the result in Streamlit, and stores completed
analyses in a local SQLite database.

The first milestone focuses on AI/software implementation, solutions and technical
consulting, and AI product roles. It intentionally avoids browser automation,
job-board circumvention, automated applications, résumé rewriting, and paid
infrastructure.

## What it does

- Extracts text from a text-based PDF résumé with `pypdf`.
- Fetches a public `http` or `https` job URL with a transparent user agent.
- Prefers schema.org `JobPosting` JSON-LD, then falls back to readable page text.
- Leaves the job description editable and supports manual paste when retrieval fails.
- Blocks analysis until both sources contain usable text.
- Calls Gemini through Google's official `google-genai` Python SDK.
- Validates every AI response with a strict Pydantic schema.
- Displays matched requirements, gaps, transferable strengths, suggestions, interview
  topics, uncertainties, a fit score, and a reasoned recommendation.
- Saves completed analyses and their source text to local SQLite history.

## Requirements

- Windows 10 or 11
- Python 3.11 or newer (3.12 is a good choice)
- A free Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)

The default `gemini-3.5-flash-lite` model and the official SDK were verified against
Google's documentation in August 2026. It is Google's current stable, structured-output
Flash-Lite model and has free-tier input and output usage. Model availability and quotas
can change, so consult the [Gemini models](https://ai.google.dev/gemini-api/docs/models)
and [pricing](https://ai.google.dev/gemini-api/docs/pricing) pages if setup fails. Do not
enable billing for this MVP.

## Windows PowerShell setup

### 1. Install Python

In a regular PowerShell terminal, install Python 3.12 with Windows Package Manager:

```powershell
winget install --id Python.Python.3.12 -e
```

Close and reopen VS Code after installation, then confirm:

```powershell
py -3.12 --version
```

Alternatively, install Python from [python.org](https://www.python.org/downloads/windows/)
and select the installer option that adds the Python launcher.

### 2. Create and activate a virtual environment

Run these commands from the repository root:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

If PowerShell blocks activation for the current process:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

For development, including tests and linting:

```powershell
python -m pip install -r requirements-dev.txt
```

For app-only use, `requirements.txt` is sufficient.

### 4. Configure Gemini

Copy the safe template, then edit `.env` in VS Code:

```powershell
Copy-Item .env.example .env
```

Set your key and keep the default model unless you intentionally choose another
free-tier model:

```dotenv
GEMINI_API_KEY=paste_your_real_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
CAREER_AGENT_DB_PATH=data/career_agent.db
```

Never commit `.env`. It and alternative local environment files are ignored by Git.

### 5. Run the app

```powershell
python -m streamlit run app.py
```

Streamlit prints a local URL, normally `http://localhost:8501`. Upload a text-based PDF,
enter a public job URL, review or paste the job description, and select **Analyze fit
with Gemini**.

### 6. Run checks

```powershell
python -m pytest
python -m ruff check .
python -m ruff format --check .
```

Automated tests mock all Gemini calls. They never require an API key or consume quota.

## Assessment evaluation

An opt-in evaluation harness uses one fictional resume and six fictional job postings.
Run one case with one Gemini call:

```powershell
python -m evaluation.runner --case-id software_implementation_strong
```

Run all six only with explicit confirmation:

```powershell
python -m evaluation.runner --all --confirm-all
```

Repetitions multiply the call count; the runner displays the total before starting.
Private reports go to ignored `data/evaluations/` and never enter application history.
See [the evaluation guide](docs/EVALUATION.md) for the human rubric, cost controls, and
limitations. Automated tests always use a mock provider and consume no Gemini quota.

## Local data and privacy

Completed analyses are stored by default in `data/career_agent.db`. That directory,
SQLite files, uploaded-document locations, extracted-text filenames, logs, and local
environment files are ignored by Git. The app processes uploaded PDF bytes in memory;
it does not save the original PDF.

The project is local-first, but AI analysis is not fully offline: the extracted résumé
text and job description are sent to the configured Google Gemini cloud model. Free-tier
usage may be used by the provider to improve its products. Review Google's current
[Gemini API terms and data-use information](https://ai.google.dev/gemini-api/terms)
before sending personal or confidential information.

## Project structure

```text
CareerAgentSystem/
├── app.py
├── career_agent/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── job_extractor.py
│   ├── models.py
│   ├── pdf_extractor.py
│   └── provider.py
├── tests/
│   ├── conftest.py
│   ├── test_database.py
│   ├── test_job_extractor.py
│   ├── test_models.py
│   ├── test_pdf_extractor.py
│   └── test_provider.py
├── .env.example
├── .gitignore
├── LICENSE
├── pyproject.toml
├── requirements-dev.txt
└── requirements.txt
```

The interface, database, and extraction logic depend on the `Assessment` domain model,
not directly on Gemini. All Gemini-specific imports and API calls live in
`career_agent/provider.py`, keeping a future provider change localized without building
an unnecessary general framework now.

## Troubleshooting

**`python` or `py` is not recognized**

Install Python as shown above, then fully restart VS Code so its terminal receives the
updated PATH. In VS Code, select the `.venv` interpreter with **Python: Select
Interpreter** from the Command Palette.

**PowerShell will not activate `.venv`**

Use the process-scoped execution-policy command in the setup section. It affects only
the current terminal session.

**The PDF has no extractable text**

The PDF is probably a scan or image. This MVP deliberately has no OCR. Export a
text-based PDF from the source document and upload it again.

**The job page is blocked or has too little text**

Some sites reject automated requests or render content only with JavaScript. The app
does not bypass those controls. Copy the complete posting in your browser and paste it
into the editable text area.

**Gemini says the API key is missing or authentication failed**

Confirm `.env` exists in the repository root, the key is named `GEMINI_API_KEY`, and no
quotes or placeholder text remain. Restart Streamlit after editing `.env`.

**Gemini reports a quota or rate limit**

Wait for the free-tier limit to reset and retry. Do not enable billing for this project.
Google can change model-specific quotas; check its current pricing and rate-limit pages.

**Gemini returns malformed output**

The app rejects it rather than saving unreliable data. Retry once. If it persists,
confirm the configured model supports structured output.

**The database cannot be opened**

Confirm the project folder is writable and `CAREER_AGENT_DB_PATH` points to a local
path. OneDrive file locking can occasionally interfere; close other programs accessing
the database and retry.

## Known limitations

- There is no OCR for scanned PDFs.
- Basic HTTP extraction cannot read JavaScript-only, authenticated, CAPTCHA-protected,
  or automation-blocking pages.
- Generic readable-text extraction may include unrelated page content.
- AI judgments can be incomplete or mistaken despite schema validation; review the
  cited evidence yourself.
- SQLite stores sensitive source text unencrypted on the local machine.
- History is intentionally simple: no search, delete, export, users, or migrations.

## License

MIT. See [LICENSE](LICENSE).
