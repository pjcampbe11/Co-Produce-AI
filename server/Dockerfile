# Co-Produce AI SaaS image - serves the API and runs as the worker (same image).
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*
# server deps + the toolkit deps the worker needs to actually run jobs
COPY server/requirements.txt server/requirements.txt
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r server/requirements.txt -r requirements.txt
COPY scripts/ scripts/
COPY server/ server/
ENV PYTHONUNBUFFERED=1 RESULTS_DIR=/data/results
EXPOSE 8000
# Default command runs the API; the worker service overrides this in compose.
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]
