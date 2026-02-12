from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Literal, Tuple

FileKind = Literal["pdf", "docx", "image"]

PDF_MIME = "application/pdf"
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def detect_file_kind(file_name: str, content_type: str | None) -> FileKind:
    normalized_content_type = str(content_type or "").split(";")[0].strip().lower()
    suffix = Path(file_name or "").suffix.lower()

    if normalized_content_type.startswith("image/"):
        return "image"
    if normalized_content_type == PDF_MIME or suffix == ".pdf":
        return "pdf"
    if normalized_content_type == DOCX_MIME or suffix == ".docx":
        return "docx"

    raise ValueError("Unsupported file type. Upload PDF, DOCX, or image.")


def normalize_extracted_text(value: str) -> str:
    text = str(value or "")
    text = text.replace("\r\n", "\n")
    text = re.sub(r"!\[[^\]]*\]\(([^)]+)\)", " ", text)
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*>\s?", "", text, flags=re.MULTILINE)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"__([^_]+)__", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"^\|?[-:\s|]+\|?$", "", text, flags=re.MULTILINE)
    text = text.replace("|", " ")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def read_first_markdown(root_dir: Path) -> str:
    markdown_files = sorted(root_dir.rglob("*.md"))
    for markdown_path in markdown_files:
        raw = markdown_path.read_text(encoding="utf-8", errors="ignore")
        cleaned = normalize_extracted_text(raw)
        if cleaned:
            return cleaned
    return ""


def parse_pdf(pdf_path: Path, stem: str) -> str:
    from doctra.parsers.structured_pdf_parser import StructuredPDFParser

    parser = StructuredPDFParser()
    parser.parse(str(pdf_path))
    output_root = Path("outputs") / stem
    expected = output_root / "full_parse" / "result.md"
    if expected.exists():
        return normalize_extracted_text(expected.read_text(encoding="utf-8", errors="ignore"))
    return read_first_markdown(output_root)


def parse_docx(docx_path: Path, stem: str) -> str:
    from doctra.parsers.structured_docx_parser import StructuredDOCXParser

    parser = StructuredDOCXParser(
        extract_images=False,
        table_detection=True,
        export_excel=False,
    )
    parser.parse(str(docx_path))
    output_root = Path("outputs") / stem
    expected = output_root / "document.md"
    if expected.exists():
        return normalize_extracted_text(expected.read_text(encoding="utf-8", errors="ignore"))
    return read_first_markdown(output_root)


def parse_image(image_path: Path) -> str:
    from PIL import Image
    from doctra.engines.ocr.api import ocr_image

    with Image.open(image_path) as img:
        # Convert to RGB so OCR gets a normalized image mode.
        normalized = img.convert("RGB")
    return normalize_extracted_text(ocr_image(normalized, lang="eng", psm=4, oem=3))


def extract_text(file_path: Path, file_name: str, content_type: str | None) -> Tuple[str, FileKind]:
    kind = detect_file_kind(file_name=file_name, content_type=content_type)
    stem = file_path.stem
    output_root = Path("outputs") / stem

    try:
        if kind == "pdf":
            text = parse_pdf(file_path, stem)
        elif kind == "docx":
            text = parse_docx(file_path, stem)
        else:
            text = parse_image(file_path)
    finally:
        if output_root.exists():
            shutil.rmtree(output_root, ignore_errors=True)

    return text, kind
