from pathlib import Path
from app.services.resume.parser import parse_resume, _structure_from_text

FIXTURE = Path(__file__).parent.parent.parent / "fixtures/resumes/simple.pdf"
DOCX_FIXTURE = Path(__file__).parent.parent.parent / "fixtures/resumes/simple.docx"


def test_parser_pdf_returns_resume_document_json():
    with FIXTURE.open("rb") as f:
        doc = parse_resume(f.read(), filename="simple.pdf")
    assert doc.contact.name == "Test User"
    assert len(doc.experience) >= 1
    assert doc.experience[0].company.lower().startswith("acme")
    assert len(doc.experience[0].bullets) == 2
    # Bullet IDs are stable & non-empty
    assert all(b.id for b in doc.experience[0].bullets)
    # raw_text populated
    assert "Acme" in doc.raw_text


def test_parser_docx_returns_resume_document_json():
    with DOCX_FIXTURE.open("rb") as f:
        doc = parse_resume(f.read(), filename="simple.docx")
    assert doc.contact.name == "Test User"
    assert len(doc.experience) >= 1
    assert len(doc.experience[0].bullets) == 2


def test_parser_extracts_pipe_dates_bullets_and_sections():
    raw = """Nagarjun Mallesh
nagarjunmallesh@gmail.com | +1-(857)-799-0214
SUMMARY
Software Engineer with backend and AI systems experience.
TECHNICAL SKILLS
Languages: Python, TypeScript
EXPERIENCE
Systems Analyst / Software Engineer | ML Technologies LLC, Boston, MA | Jul 2025 - Present
● Built RAG-based conversational AI systems using Python FastAPI and AWS Bedrock for workforce, insurance, and EV
marketplace platforms.
● Automated AWS infrastructure using Terraform, CloudWatch, and Bash, reducing environment onboarding from 4 hours to 15
minutes.
Backend Software Engineer | Keelworks Foundation, Oak Harbor, WA | Jul 2024 - Jul 2025
▪ Built and Dockerized Node.js backend services deployed through AWS ECR for volunteer management workflows.
Software Engineer | Hewlett-Packard Inc, Bangalore, India | Oct 2019 - Jul 2022
◦ Automated BIOS configuration deployment using PowerShell, reducing a 4-day manual workflow to 15 minutes.
Associate Software Engineer | Digital API Craft Pvt Ltd, Bangalore, India | Jul 2019 - Oct 2019
* Migrated user services from a monolith to Spring Boot microservices with Kafka messaging.
NOTABLE PROJECTS
● Built a corpus-grounded support triage agent using Python, Claude, FAISS, and sentence-transformers.
EDUCATION
MS Information Systems | Northeastern University, Boston, MA | 2022-2024
BE Information Science & Engineering | Visvesvaraya Technological University, India | 2015-2019
CERTIFICATIONS
CS50's Introduction to Artificial Intelligence with Python | Harvard University | 2024
"""
    doc = _structure_from_text(raw)

    assert len(doc.experience) == 4
    assert [entry.dates for entry in doc.experience] == [
        "Jul 2025 - Present",
        "Jul 2024 - Jul 2025",
        "Oct 2019 - Jul 2022",
        "Jul 2019 - Oct 2019",
    ]
    assert doc.experience[0].company == "ML Technologies LLC"
    assert doc.experience[0].location == "Boston, MA"
    assert len(doc.experience[0].bullets) == 2
    assert "marketplace platforms" in doc.experience[0].bullets[0].text
    assert "15 minutes" in doc.experience[0].bullets[1].text
    assert len(doc.education) == 2
    assert doc.education[0].school == "Northeastern University"
    assert doc.education[0].degree == "MS Information Systems"
    assert doc.education[0].location == "Boston, MA"
    assert doc.education[0].dates == "2022-2024"
    assert doc.education[1].location == "India"
    assert doc.education[1].dates == "2015-2019"
    assert len(doc.projects) == 1
    assert len(doc.projects[0].bullets) == 1
    assert doc.certifications == [
        "CS50's Introduction to Artificial Intelligence with Python | Harvard University | 2024"
    ]


def test_parser_preserves_contact_links_for_export():
    doc = _structure_from_text(
        """Jane Doe
jane@example.com | +1 555 0100 | linkedin.com/in/janedoe | https://github.com/janedoe
SUMMARY
Backend engineer.
"""
    )

    assert doc.contact.links == [
        "https://linkedin.com/in/janedoe",
        "https://github.com/janedoe",
    ]


def test_parser_reads_canonical_export_rows_on_reupload():
    raw = """Jane Doe
jane@example.com · +1 555 0100 · https://github.com/janedoe
SUMMARY
Backend engineer.
TECHNICAL SKILLS
Python, Postgres, AWS
WORK EXPERIENCE
Senior SWE · Acme 2022-2026 · SF, CA
• Built backend APIs.
PROJECTS
OSS lib
• Built a parser.
EDUCATION
BS CS · State U 2017-2021 · GPA 3.8
"""

    doc = _structure_from_text(raw)

    assert doc.contact.links == ["https://github.com/janedoe"]
    assert doc.experience[0].role == "Senior SWE"
    assert doc.experience[0].company == "Acme"
    assert doc.experience[0].location == "SF, CA"
    assert doc.experience[0].dates == "2022-2026"
    assert doc.experience[0].bullets[0].text == "Built backend APIs."
    assert doc.education[0].degree == "BS CS"
    assert doc.education[0].school == "State U"
    assert doc.education[0].dates == "2017-2021"
    assert doc.education[0].gpa == "3.8"
