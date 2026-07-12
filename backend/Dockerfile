# SFTC backend — FastAPI + Motor. Build context is this backend/ directory.
FROM python:3.11-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8001

# System deps kept minimal; slowapi/motor/passlib are pure-python or wheels.
COPY requirements-runtime.txt .
RUN pip install --no-cache-dir -r requirements-runtime.txt

COPY . .

EXPOSE 8001
# Config comes from env (MONGO_URL, DB_NAME, JWT_SECRET, ...). See .env.example.
CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port ${PORT}"]
