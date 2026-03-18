from pathlib import Path
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import render_api.app as app_module


client = TestClient(app_module.app)


def test_extract_endpoint_returns_candidate_contract(monkeypatch):
    def fake_extract_candidate(file_path, file_name, content_type, profile=None, max_pages=None):
        assert file_name == "sample.pdf"
        assert content_type == "application/pdf"
        assert profile == "enhanced_pdf"
        assert max_pages == 5
        return {
            "backend": "doctra",
            "kind": "pdf",
            "parser": "enhanced_pdf",
            "text": "Recovered text",
            "charCount": 14,
            "pageCount": 1,
            "pages": [{
                "index": 0,
                "text": "Recovered text",
                "chars": 14,
                "tableCount": 0,
                "formulaCount": 0,
                "source": "doctra",
            }],
            "warnings": [],
            "metrics": {
                "tableCount": 0,
                "formulaCount": 0,
                "chartCount": 0,
            },
        }

    monkeypatch.setattr(app_module, "extract_candidate", fake_extract_candidate)

    response = client.post(
        "/extract",
        files={"file": ("sample.pdf", b"pdf-bytes", "application/pdf")},
        data={
            "contentType": "application/pdf",
            "profile": "enhanced_pdf",
            "maxPages": "5",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["backend"] == "doctra"
    assert payload["kind"] == "pdf"
    assert payload["parser"] == "enhanced_pdf"
    assert payload["text"] == "Recovered text"
    assert payload["pageCount"] == 1
    assert payload["pages"][0]["source"] == "doctra"
