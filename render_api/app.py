from __future__ import annotations

import os
import tempfile
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
from starlette.concurrency import run_in_threadpool

from render_api.extract_service import extract_candidate

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024
DOCTRA_SHARED_SECRET = str(os.getenv("DOCTRA_SHARED_SECRET", "")).strip()

app = FastAPI(title="Doctra Parser API", version="1.0.0")


@app.get("/health")
def health_check():
    return {"ok": True, "service": "doctra-parser-api"}


@app.post("/extract")
async def extract_endpoint(
    file: UploadFile = File(...),
    contentType: str | None = Form(default=None),
    profile: str | None = Form(default=None),
    maxPages: int | None = Form(default=None),
    x_doctra_shared_secret: str | None = Header(default=None, alias="x-doctra-shared-secret"),
):
    if DOCTRA_SHARED_SECRET and x_doctra_shared_secret != DOCTRA_SHARED_SECRET:
        raise HTTPException(status_code=401, detail="Invalid shared secret.")

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
        candidate = await run_in_threadpool(
            extract_candidate,
            tmp_path,
            file.filename,
            detected_content_type,
            profile,
            maxPages,
        )
        if not str(candidate.get("text", "")).strip():
            raise HTTPException(
                status_code=422,
                detail="Could not extract readable text from this file.",
            )
        return candidate
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
