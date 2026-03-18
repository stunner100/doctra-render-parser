from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from render_api.extract_service import (
    build_candidate_pages,
    default_profile_for_kind,
    detect_file_kind,
    normalize_extracted_text,
    normalize_requested_profile,
)


def test_detect_file_kind_from_mime():
    assert detect_file_kind("lecture.pdf", "application/pdf") == "pdf"
    assert (
        detect_file_kind(
            "worksheet.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        == "docx"
    )
    assert detect_file_kind("photo.jpg", "image/jpeg") == "image"


def test_detect_file_kind_from_extension_fallback():
    assert detect_file_kind("notes.pdf", None) == "pdf"
    assert detect_file_kind("notes.docx", "") == "docx"


def test_markdown_cleanup_regression():
    raw = """# Title

![figure](images/a.png)
**Bold** and _plain_ text.

| A | B |
|---|---|
| 1 | 2 |
"""
    cleaned = normalize_extracted_text(raw)
    assert "Title" in cleaned
    assert "Bold and _plain_ text." in cleaned
    assert "figure" not in cleaned.lower()
    assert "|" not in cleaned


def test_profile_defaults_and_validation():
    assert default_profile_for_kind("pdf") == "basic_pdf"
    assert default_profile_for_kind("docx") == "docx_structured"
    assert default_profile_for_kind("image") == "image_ocr"
    assert normalize_requested_profile("pdf", "enhanced_pdf") == "enhanced_pdf"


def test_candidate_page_builder_preserves_page_boundaries():
    pages = build_candidate_pages("First page text\fSecond page text")
    assert len(pages) == 2
    assert pages[0]["index"] == 0
    assert pages[1]["index"] == 1
    assert "First page text" in pages[0]["text"]
    assert "Second page text" in pages[1]["text"]


if __name__ == "__main__":
    test_detect_file_kind_from_mime()
    test_detect_file_kind_from_extension_fallback()
    test_markdown_cleanup_regression()
    test_profile_defaults_and_validation()
    test_candidate_page_builder_preserves_page_boundaries()
    print("render_api utility regression tests passed")
