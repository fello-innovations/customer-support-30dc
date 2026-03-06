FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/
COPY "HANDBOOK_MAIN (2).md" .
COPY scripts/ ./scripts/

# Non-root user for security
RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE ${PORT:-8000}

CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2
