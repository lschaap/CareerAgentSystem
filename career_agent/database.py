"""Straightforward SQLite persistence for completed analyses."""

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from career_agent.models import AnalysisRecord, Assessment


class DatabaseError(RuntimeError):
    """Raised when local persistence fails."""


SCHEMA = """
CREATE TABLE IF NOT EXISTS analyses (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    job_url TEXT NOT NULL,
    job_title TEXT NOT NULL,
    company_name TEXT NOT NULL,
    job_description TEXT NOT NULL,
    resume_text TEXT NOT NULL,
    model_used TEXT NOT NULL,
    assessment_json TEXT NOT NULL
)
"""


class AnalysisRepository:
    def __init__(self, database_path: Path | str):
        self.database_path = Path(database_path)

    def _connect(self) -> sqlite3.Connection:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        try:
            with self._connect() as connection:
                connection.execute(SCHEMA)
        except sqlite3.Error as exc:
            raise DatabaseError("Could not initialize the local analysis database.") from exc

    def save(
        self,
        *,
        job_url: str,
        job_description: str,
        resume_text: str,
        model_used: str,
        assessment: Assessment,
    ) -> AnalysisRecord:
        record = AnalysisRecord(
            id=str(uuid4()),
            created_at=datetime.now(UTC),
            job_url=job_url,
            job_title=assessment.job_title,
            company_name=assessment.company_name,
            job_description=job_description,
            resume_text=resume_text,
            model_used=model_used,
            assessment=assessment,
        )
        try:
            with self._connect() as connection:
                connection.execute(
                    """INSERT INTO analyses
                    (id, created_at, job_url, job_title, company_name, job_description,
                     resume_text, model_used, assessment_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        record.id,
                        record.created_at.isoformat(),
                        record.job_url,
                        record.job_title,
                        record.company_name,
                        record.job_description,
                        record.resume_text,
                        record.model_used,
                        record.assessment.model_dump_json(),
                    ),
                )
        except sqlite3.Error as exc:
            raise DatabaseError("The completed analysis could not be saved locally.") from exc
        return record

    def list(self, limit: int = 50) -> list[AnalysisRecord]:
        try:
            with self._connect() as connection:
                rows = connection.execute(
                    "SELECT * FROM analyses ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
        except sqlite3.Error as exc:
            raise DatabaseError("Saved analysis history could not be loaded.") from exc
        return [self._row_to_record(row) for row in rows]

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> AnalysisRecord:
        return AnalysisRecord(
            id=row["id"],
            created_at=datetime.fromisoformat(row["created_at"]),
            job_url=row["job_url"],
            job_title=row["job_title"],
            company_name=row["company_name"],
            job_description=row["job_description"],
            resume_text=row["resume_text"],
            model_used=row["model_used"],
            assessment=Assessment.model_validate(json.loads(row["assessment_json"])),
        )
