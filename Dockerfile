FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    tesseract-ocr \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . /app

RUN pip install --upgrade pip setuptools wheel && \
    pip install . && \
    pip install fastapi "uvicorn[standard]" python-multipart

EXPOSE 10000

CMD ["sh", "-c", "uvicorn render_api.app:app --host 0.0.0.0 --port ${PORT:-10000}"]

