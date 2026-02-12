from __future__ import annotations

import tempfile
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from starlette.concurrency import run_in_threadpool

from render_api.extract_service import extract_text

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024

app = FastAPI(title="Doctra Parser API", version="1.0.0")


@app.get("/health")
def health_check():
    return {"ok": True, "service": "doctra-parser-api"}


@app.post("/extract")
async def extract_endpoint(
    file: UploadFile = File(...),
    contentType: str | None = Form(default=None),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing file name.")

    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(payload) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 50MB limit.")

    suffix = Path(file.filename).suffix or ""
    tmp_name = f"{uuid4().hex}{suffix}"
    tmp_path = Path(tempfile.gettempdir()) / tmp_name
    tmp_path.write_bytes(payload)

    detected_content_type = contentType or file.content_type

    try:
        text, kind = await run_in_threadpool(
            extract_text,
            tmp_path,
            file.filename,
            detected_content_type,
        )
        if not text.strip():
            raise HTTPException(
                status_code=422,
                detail="Could not extract readable text from this file.",
            )
        return {
            "kind": kind,
            "text": text,
            "charCount": len(text),
        }
    except HTTPException:
        raise
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {error}") from error
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass

