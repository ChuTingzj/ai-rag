from __future__ import annotations

from pathlib import Path

_MIME_ALIASES = {
    ".md": "text/markdown",
    ".markdown": "text/markdown",
    ".txt": "text/plain",
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def parse_file(path: Path, mime_type: str | None = None) -> str:
    resolved_mime = mime_type or _guess_mime(path)
    data = path.read_bytes()
    return parse_bytes(data, resolved_mime, path.name)


def parse_bytes(data: bytes, mime_type: str | None, filename: str = "") -> str:
    mime = mime_type or _guess_mime(Path(filename))
    if mime in ("text/plain", "text/markdown"):
        return data.decode("utf-8", errors="replace")
    if mime == "application/pdf":
        return _parse_pdf(data)
    if mime == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return _parse_docx(data)
    suffix = Path(filename).suffix.lower()
    if suffix in (".md", ".markdown", ".txt"):
        return data.decode("utf-8", errors="replace")
    if suffix == ".pdf":
        return _parse_pdf(data)
    if suffix == ".docx":
        return _parse_docx(data)
    raise ValueError(f"Unsupported document type: {mime or filename}")


def _guess_mime(path: Path) -> str:
    return _MIME_ALIASES.get(path.suffix.lower(), "application/octet-stream")


def _parse_pdf(data: bytes) -> str:
    import fitz

    doc = fitz.open(stream=data, filetype="pdf")
    try:
        parts = [page.get_text("text") for page in doc]
    finally:
        doc.close()
    return "\n\n".join(p.strip() for p in parts if p.strip())


def _parse_docx(data: bytes) -> str:
    from io import BytesIO

    from docx import Document

    document = Document(BytesIO(data))
    return "\n".join(p.text for p in document.paragraphs if p.text.strip())
