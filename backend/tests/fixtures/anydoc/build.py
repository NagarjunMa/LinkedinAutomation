"""Generate only synthetic PRI-19 documents and independent expected labels."""
import hashlib
import json
from pathlib import Path
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED
from docx import Document
from PIL import Image, ImageDraw
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from app.services.resume.parser import _structure_from_text
from app.services.pdf.renderer import render_pdf_from_doc

ROOT = Path(__file__).parent
LINES = ["Alex Example", "alex@example.invalid", "EXPERIENCE",
         "Engineer | Example Labs | 2020-2024", "- Built a parser.",
         "EDUCATION", "BS Computing | Example University | 2016-2020",
         "SKILLS", "Python, SQL"]
FIELDS = {"contact.name": "Alex Example", "contact.email": "alex@example.invalid",
          "experience.0.company": "Example Labs", "experience.0.role": "Engineer",
          "experience.0.dates": "2020-2024", "experience.0.bullets.0.text": "Built a parser.",
          "education.0.school": "Example University", "skills.hard.0": "Python"}
manifest = []


def save(name, content, fields=FIELDS, order=None):
    (ROOT / name).write_bytes(content)
    manifest.append({"file": name, "provenance": "synthetic PRI-19; no real person",
                     "sha256": hashlib.sha256(content).hexdigest(), "fields": fields,
                     "order": order if order is not None else ["Alex Example", "EXPERIENCE", "EDUCATION", "SKILLS"]})


for variant in ("simple", "columns", "linkedin-style", "scanned", "over-page-limit"):
    stream = BytesIO()
    pdf = canvas.Canvas(stream, pagesize=(612, 792), invariant=1)
    pdf.setFont("Helvetica", 10)
    if variant == "scanned":
        image = Image.new("RGB", (1000, 500), "white")
        ImageDraw.Draw(image).multiline_text((30, 30), "\n".join(LINES), fill="black", spacing=12)
        pdf.drawImage(ImageReader(image), 36, 420, width=540, height=270)
    else:
        lines = LINES if variant != "linkedin-style" else ["Contact", "alex@example.invalid", "Top Skills", "Python", "SQL", "Alex Example", "Backend Engineer", "Experience", "Example Labs", "Engineer", "2020-2024", "Built a parser.", "Education", "Example University", "BS Computing", "2016-2020"]
        for i, line in enumerate(lines):
            column = variant == "columns" and i >= 5
            pdf.drawString(320 if column else 36, 740 - (i - 5 if column else i) * 24, line)
    if variant == "over-page-limit":
        for _ in range(11):
            pdf.showPage()
    pdf.save()
    save(variant + ".pdf", stream.getvalue(), {} if variant in ("scanned", "over-page-limit") else FIELDS,
         ["Alex Example", "Experience", "Education"] if variant == "linkedin-style" else None)
doc = Document()
for line in LINES:
    doc.add_paragraph(line)
stream = BytesIO()
doc.save(stream)
save("simple.docx", stream.getvalue())
save("prism-export.pdf", render_pdf_from_doc(_structure_from_text("\n".join(LINES)), "US", "swe"),
     order=["Alex Example", "WORK EXPERIENCE", "EDUCATION"])
save("malformed.pdf", b"%PDF-1.7\ninvalid", {}, [])
stream = BytesIO()
with ZipFile(stream, "w", ZIP_DEFLATED) as archive:
    archive.writestr("../escape", "invalid")
save("unsafe.docx", stream.getvalue(), {}, [])
(ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
