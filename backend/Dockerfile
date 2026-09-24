FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY backend ./backend
RUN python -m pip install --no-cache-dir --require-hashes -r backend/requirements.lock \
    && python -m pip install --no-cache-dir --no-deps --no-build-isolation .
COPY alembic.ini ./
EXPOSE 8000
CMD ["sh", "-c", "python -m alembic upgrade head && python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000"]
