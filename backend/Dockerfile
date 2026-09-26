FROM python:3.12.14-slim-trixie

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        libgl1=1.7.0-1+b2 \
        libglib2.0-0=2.84.4-3~deb13u5 \
        libgomp1=14.2.0-19 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# /models/ocr is the target for the deployment's external read-only model
# mount. The Paddle caches remain separate and writable by the image's
# existing root execution user.
ENV QA_OCR_MODEL_ROOT=/models/ocr \
    PADDLE_HOME=/var/cache/paddle \
    PADDLE_PDX_CACHE_HOME=/var/cache/paddle
RUN mkdir -p /models/ocr /var/cache/paddle \
    && chmod 0755 /var/cache/paddle

COPY pyproject.toml ./
COPY backend ./backend
COPY worker ./worker
RUN python -m pip install --no-cache-dir --require-hashes -r backend/requirements.lock \
    && python -m pip install --no-cache-dir --no-deps --no-build-isolation . \
    && python -m pip check
COPY alembic.ini ./
EXPOSE 8000
CMD ["sh", "-c", "python -m alembic upgrade head && python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000"]
