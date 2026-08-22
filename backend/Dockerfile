FROM python:3.12-slim AS runtime

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

COPY backend/requirements-runtime.txt ./backend/requirements-runtime.txt
RUN pip install --no-cache-dir -r backend/requirements-runtime.txt

COPY backend/__init__.py ./backend/__init__.py
COPY backend/app ./backend/app
COPY backend/alembic ./backend/alembic
COPY alembic.ini ./alembic.ini

RUN useradd --create-home --uid 10001 runlete && chown -R runlete:runlete /app
USER runlete
EXPOSE 8080
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT} --proxy-headers"]
