"""Streamlit entry point for Career Agent MVP."""

import os

import streamlit as st
from dotenv import load_dotenv

from career_agent.config import load_settings
from career_agent.database import AnalysisRepository, DatabaseError
from career_agent.job_extractor import JobExtractionError, ensure_adequate, fetch_job
from career_agent.models import Assessment
from career_agent.pdf_extractor import PDFExtractionError, extract_pdf_text
from career_agent.provider import AIProviderError, analyze_with_gemini

load_dotenv()
st.set_page_config(page_title="Career Agent MVP", page_icon="🎯", layout="wide")


def show_technical_details(exc: Exception) -> None:
    with st.expander("Technical details"):
        st.code(f"{type(exc).__name__}: {exc.__cause__ or exc}")


def render_assessment(assessment: Assessment) -> None:
    st.header(f"{assessment.job_title} — {assessment.company_name}")
    score, recommendation = st.columns([1, 3])
    score.metric("Fit score", f"{assessment.fit_score}/100")
    recommendation.subheader(assessment.recommendation)
    recommendation.write(assessment.recommendation_reasoning)

    sections = [
        ("Matched requirements", assessment.matched_requirements),
        ("Missing requirements", assessment.missing_requirements),
    ]
    for heading, items in sections:
        st.subheader(heading)
        if not items:
            st.caption("None identified.")
        for item in items:
            if hasattr(item, "evidence"):
                st.markdown(
                    f"- **{item.requirement}** ({item.qualification_type}): {item.evidence}"
                )
            else:
                st.markdown(
                    f"- **{item.requirement}** ({item.qualification_type}): {item.explanation}"
                )

    list_sections = [
        ("Transferable strengths", assessment.transferable_strengths),
        ("Résumé tailoring suggestions", assessment.resume_tailoring_suggestions),
        ("Likely interview topics", assessment.likely_interview_topics),
        ("Uncertainties or missing information", assessment.uncertainties_or_missing_information),
    ]
    for heading, items in list_sections:
        st.subheader(heading)
        if items:
            for item in items:
                st.markdown(f"- {item}")
        else:
            st.caption("None identified.")


def analysis_view(repository: AnalysisRepository) -> None:
    st.title("Career Agent MVP")
    st.write("Compare one PDF résumé with one job posting and save a structured assessment.")
    st.info(
        "Privacy: résumé and job text stay local except when sent to the configured Gemini API. "
        "Review Google's free-tier data policies before using personal information."
    )

    uploaded = st.file_uploader("1. Upload your résumé (PDF)", type=["pdf"])
    resume_text = ""
    if uploaded:
        try:
            resume_text = extract_pdf_text(uploaded.getvalue())
            st.success(f"Extracted résumé text ({len(resume_text):,} characters).")
        except PDFExtractionError as exc:
            st.error(str(exc))
            show_technical_details(exc)

    job_url = st.text_input("2. Job-posting URL", placeholder="https://example.com/jobs/role")
    if "job_text" not in st.session_state:
        st.session_state.job_text = ""
    if st.button("Extract job description", disabled=not job_url.strip()):
        try:
            extracted = fetch_job(job_url.strip())
            st.session_state.job_text = extracted.text
            st.success(f"Extracted from {extracted.source}. Review and edit it below.")
        except JobExtractionError as exc:
            st.warning(str(exc))
            show_technical_details(exc)

    job_text = st.text_area(
        "3. Job description (editable; paste it here if extraction fails)",
        key="job_text",
        height=350,
        placeholder="Paste the complete job description here.",
    )

    usable_job = False
    if job_text.strip():
        try:
            ensure_adequate(job_text)
            usable_job = True
        except JobExtractionError as exc:
            st.warning(str(exc))

    settings = load_settings()
    ready = bool(resume_text and usable_job)
    if not ready:
        st.caption(
            "Analysis unlocks after a readable PDF and a complete job description are present."
        )

    if st.button("Analyze fit with Gemini", type="primary", disabled=not ready):
        try:
            with st.spinner("Gemini is comparing the evidence..."):
                assessment = analyze_with_gemini(
                    resume_text,
                    ensure_adequate(job_text),
                    settings.gemini_api_key,
                    settings.gemini_model,
                )
                record = repository.save(
                    job_url=job_url.strip(),
                    job_description=job_text,
                    resume_text=resume_text,
                    model_used=settings.gemini_model,
                    assessment=assessment,
                )
            st.session_state.latest_assessment = assessment
            st.success(f"Analysis saved locally with ID {record.id}.")
        except (AIProviderError, DatabaseError) as exc:
            st.error(str(exc))
            show_technical_details(exc)

    if assessment := st.session_state.get("latest_assessment"):
        render_assessment(assessment)


def history_view(repository: AnalysisRepository) -> None:
    st.title("Analysis history")
    try:
        records = repository.list()
    except DatabaseError as exc:
        st.error(str(exc))
        show_technical_details(exc)
        return
    if not records:
        st.info("No completed analyses have been saved yet.")
    for record in records:
        label = (
            f"{record.created_at.astimezone().strftime('%Y-%m-%d %H:%M')} — "
            f"{record.job_title} at {record.company_name} ({record.assessment.fit_score}/100)"
        )
        with st.expander(label):
            st.caption(
                f"ID: {record.id} | Model: {record.model_used} | URL: {record.job_url or 'None'}"
            )
            render_assessment(record.assessment)
            with st.expander("Stored source text"):
                st.text_area("Job description", record.job_description, height=200, disabled=True)
                st.text_area("Résumé text", record.resume_text, height=200, disabled=True)


def main() -> None:
    settings = load_settings()
    repository = AnalysisRepository(settings.database_path)
    try:
        repository.initialize()
    except DatabaseError as exc:
        st.error(str(exc))
        show_technical_details(exc)
        st.stop()

    page = st.sidebar.radio("View", ["New analysis", "History"])
    st.sidebar.caption(f"Model: {settings.gemini_model}")
    if not os.getenv("GEMINI_API_KEY"):
        st.sidebar.warning("GEMINI_API_KEY is not configured.")
    if page == "New analysis":
        analysis_view(repository)
    else:
        history_view(repository)


if __name__ == "__main__":
    main()
