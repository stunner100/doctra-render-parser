from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from render_api.extract_service import detect_file_kind, normalize_extracted_text


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


if __name__ == "__main__":
    test_detect_file_kind_from_mime()
    test_detect_file_kind_from_extension_fallback()
    test_markdown_cleanup_regression()
    print("render_api utility regression tests passed")
