# Beat Toolkit - RunPod Serverless worker image.
# GPU base (CUDA 12.1) because generation/flip tasks need it; the heuristic
# tagger runs fine here too. Build for linux/amd64 (RunPod requirement).
FROM runpod/base:0.6.2-cuda12.1.0

WORKDIR /app

# Install Python deps first so Docker layer-caches them across code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt runpod

# Copy the toolkit scripts and the handler.
COPY scripts/ scripts/
COPY serverless/handler.py .

# Unbuffered so logs stream live in the RunPod console.
CMD ["python", "-u", "handler.py"]
