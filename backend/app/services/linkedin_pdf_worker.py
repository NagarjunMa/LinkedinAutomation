"""Extract bounded PDF page text in a subprocess without application credentials."""

import json
import sys
from io import BytesIO

import pdfplumber


def _extract_text(page) -> tuple[str, int | None]:
    # LinkedIn exports commonly place Contact and Top Skills in a left sidebar.
    left, top, right, bottom = page.bbox
    gutter = left + (right - left) * 0.32
    sidebar = (page.crop((left, top, gutter, bottom)).extract_text() or "").rstrip("\r\n")
    if "contact" in {line.strip().casefold() for line in sidebar.splitlines()}:
        main = page.crop((gutter, top, right, bottom)).extract_text() or ""
        if {"summary", "about", "experience", "education"} & {
            line.strip().casefold() for line in main.splitlines()
        }:
            return sidebar + "\n" + main, len(sidebar.splitlines())
    return page.extract_text() or "", None


def main() -> None:
    try:
        size, page_limit, char_limit = map(int, sys.argv[1:])
        if sys.platform.startswith("linux"):
            import resource

            address_space = 192 * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (address_space, address_space))
        data = sys.stdin.buffer.read(size + 1)
        if len(data) > size:
            print(json.dumps({"ok": False, "error_type": "too_large"}))
            return
        pages = []
        length = 0
        sidebar_lines = []
        with pdfplumber.open(BytesIO(data)) as pdf:
            if not 0 < len(pdf.pages) <= page_limit:
                print(json.dumps({"ok": False, "error_type": "complexity", "message": "PDF page limit exceeded"}))
                return
            for page in pdf.pages:
                content, last_sidebar_line = _extract_text(page)
                sidebar_lines.append(last_sidebar_line)
                content = content.replace("\x00", "")
                length += len(content) + bool(pages)
                if length > char_limit:
                    print(json.dumps({"ok": False, "error_type": "complexity", "message": "PDF text limit exceeded"}))
                    return
                pages.append(content)
                page.close()
        print(json.dumps({"ok": True, "pages": pages, "sidebar_lines": sidebar_lines}))
    except MemoryError:
        print(json.dumps({"ok": False, "error_type": "complexity", "message": "PDF processing limit exceeded"}))
    except Exception:
        print(json.dumps({"ok": False, "error_type": "validation", "message": "PDF could not be parsed"}))


if __name__ == "__main__":
    main()
