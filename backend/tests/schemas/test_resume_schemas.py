from app.schemas.resume_v2 import ResumeDocumentJSON, Bullet, ExperienceEntry, Skills


def test_resume_document_json_roundtrip():
    doc = ResumeDocumentJSON(
        contact={"name": "Asha", "email": "a@b.com", "phone": "+91...", "links": []},
        summary="Senior SWE...",
        experience=[ExperienceEntry(
            company="Acme", role="SWE II", dates="2022-2024", location="Bengaluru",
            bullets=[Bullet(id="b1", text="Led migration", raw_text="Led migration")]
        )],
        education=[],
        skills=Skills(hard=["Python"], soft=["communication"]),
        raw_text="full text..."
    )
    serialized = doc.model_dump()
    assert serialized["experience"][0]["bullets"][0]["id"] == "b1"
