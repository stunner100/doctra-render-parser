from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import render_api.extract_service as extract_service


class FakeParser:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.parsed_path = None

    def parse(self, document_path):
        self.parsed_path = document_path


def test_select_pdf_parser_enhanced(monkeypatch):
    monkeypatch.setattr(extract_service, "load_enhanced_pdf_parser_cls", lambda: FakeParser)

    parser = extract_service.select_pdf_parser("enhanced_pdf")

    assert isinstance(parser, FakeParser)
    assert parser.kwargs["use_image_restoration"] is True
    assert parser.kwargs["merge_split_tables"] is True


def test_select_pdf_parser_paddleocr_vl(monkeypatch):
    monkeypatch.setattr(extract_service, "load_paddleocr_vl_parser_cls", lambda: FakeParser)

    parser = extract_service.select_pdf_parser("paddleocr_vl")

    assert isinstance(parser, FakeParser)
    assert parser.kwargs["use_image_restoration"] is True
    assert parser.kwargs["use_chart_recognition"] is True
    assert parser.kwargs["merge_split_tables"] is True


def test_extract_candidate_uses_docx_profile(monkeypatch, tmp_path):
    docx_path = tmp_path / "notes.docx"
    docx_path.write_bytes(b"docx")

    monkeypatch.setattr(
        extract_service,
        "parse_docx",
        lambda path, stem, profile: ("Structured docx text", [], {
            "tableCount": 0,
            "formulaCount": 0,
            "chartCount": 0,
        }),
    )

    candidate = extract_service.extract_candidate(
        file_path=docx_path,
        file_name="notes.docx",
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        profile="docx_structured",
    )

    assert candidate["kind"] == "docx"
    assert candidate["parser"] == "docx_structured"
    assert candidate["text"] == "Structured docx text"
    assert candidate["pageCount"] == 1


def test_invalid_profile_for_kind_raises():
    with pytest.raises(ValueError):
        extract_service.normalize_requested_profile("docx", "enhanced_pdf")
