FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000

# Install system libraries needed by OpenCV, image processing, and networking
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxcb1 \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch CPU first (saves ~2GB of CUDA bloat and prevents build timeouts on cloud hosts)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Copy requirements from backend
COPY echo-assist-ai/backend/requirements.txt ./requirements.txt

# Install remaining Python packages
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir "scikit-learn>=1.5,<2"

# Copy backend application code
COPY echo-assist-ai/backend/ ./

# Copy AI engine models and components
COPY echo-assist-ai/ai_engine/ ./ai_engine/
COPY echo-assist-ai/ai_engine/ /ai_engine/

# Ensure yolo model file is present
COPY echo-assist-ai/backend/yolo11n.pt ./yolo11n.pt

# Expose default port
EXPOSE 8000

# Run Alembic migrations if database is available, then start Uvicorn on dynamic $PORT
CMD ["sh", "-c", "alembic upgrade head || echo 'Notice: Database migration skipped or database unreachable. Proceeding with application startup...'; exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
