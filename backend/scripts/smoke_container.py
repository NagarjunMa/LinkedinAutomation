"""Exercise the built backend image's runtime permissions and real PDF renderer."""

import os
from pathlib import Path
from tempfile import TemporaryFile

from app.schemas.resume_v2 import Bullet, Contact, ExperienceEntry, ResumeDocumentJSON
from app.services.pdf.renderer import get_pdf_page_count, render_pdf_from_doc
from app.utils.logger import log_dir as legacy_log_dir


def main() -> None:
    assert os.geteuid() != 0, "backend still runs as root"
    assert os.getegid() != 0, "backend still uses the root group"
    assert legacy_log_dir == Path("/app/logs")

    for directory in (Path.home(), Path("/app/logs"), Path("/app/uploads/resumes")):
        with TemporaryFile(dir=directory):
            pass

    for directory in (Path("/app"), Path("/app/app"), Path("/ms-playwright")):
        try:
            with TemporaryFile(dir=directory):
                pass
        except PermissionError:
            continue
        raise AssertionError(f"runtime can write protected path {directory}")

    resume = ResumeDocumentJSON(
        contact=Contact(name="Container Smoke"),
        experience=[ExperienceEntry(
            company="Example", role="Engineer", dates="2022-2026",
            bullets=[Bullet(id="b1", text="Built reliable services.", raw_text="Built reliable services.")],
        )],
        raw_text="Built reliable services.",
    )
    pdf = render_pdf_from_doc(resume, country="US", role="swe")
    assert pdf.startswith(b"%PDF-") and len(pdf) > 2000
    assert get_pdf_page_count(pdf) == 1
    print(f"container smoke passed: uid={os.geteuid()}, pdf_bytes={len(pdf)}")


if __name__ == "__main__":
    main()
