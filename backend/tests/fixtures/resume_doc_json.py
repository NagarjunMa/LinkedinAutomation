"""Shared resume fixture builder for PDF template testing."""
from app.schemas.resume import (
    Bullet,
    Contact,
    EducationEntry,
    ExperienceEntry,
    ProjectEntry,
    ResumeDocumentJSON,
    Skills,
)


def make_resume(name: str = "Jane Doe") -> ResumeDocumentJSON:
    """Build a minimal but complete ResumeDocumentJSON for testing."""
    return ResumeDocumentJSON(
        contact=Contact(
            name=name,
            email="jane@example.com",
            phone="+1 555-0100",
            links=["https://github.com/janedoe"],
        ),
        summary="SWE with 5 years building distributed systems.",
        experience=[
            ExperienceEntry(
                company="Acme",
                role="Senior SWE",
                dates="2022-2026",
                location="SF, CA",
                bullets=[
                    Bullet(
                        id="b1",
                        text="Cut p99 latency 38% by rewriting the auth path.",
                        raw_text="...",
                    ),
                    Bullet(
                        id="b2",
                        text="Mentored 4 engineers; 3 promoted within 12 months.",
                        raw_text="...",
                    ),
                ],
            ),
        ],
        education=[
            EducationEntry(
                school="State U", degree="BS CS", dates="2017-2021", gpa="3.8"
            )
        ],
        skills=Skills(hard=["Python", "Postgres", "AWS"], soft=["Mentoring"]),
        projects=[
            ProjectEntry(
                name="OSS lib",
                bullets=[
                    Bullet(id="p1", text="500+ GitHub stars.", raw_text="...")
                ],
            )
        ],
        raw_text="…",
    )
