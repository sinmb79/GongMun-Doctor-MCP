"""HWPX document handler — open, iterate, save via python-hwpx."""

from pathlib import Path

from hwpx.document import HwpxDocument


def open_document(path: str | Path) -> HwpxDocument:
    """Open an HWPX file and return the document object."""
    path = Path(path)
    if path.suffix.lower() not in (".hwpx",):
        raise ValueError(f"HWPX 파일이 아닙니다: {path}")
    if not path.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {path}")
    return HwpxDocument.open(str(path))


def save_document(doc: HwpxDocument, path: str | Path) -> None:
    """Save document to path."""
    doc.save_to_path(str(path))


def extract_text(doc: HwpxDocument) -> str:
    """Return full document text."""
    return doc.export_text()


def close_document(doc: HwpxDocument) -> None:
    """Close document and release resources."""
    doc.close()
