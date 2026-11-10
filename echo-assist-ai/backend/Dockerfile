FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

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

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

COPY backend/requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir "scikit-learn>=1.5,<2"

COPY backend/ ./

COPY ai_engine/ ./ai_engine/
COPY ai_engine/ /ai_engine/
COPY yolo11n.pt ./yolo11n.pt

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head || echo 'Notice: Database migration skipped or database unreachable. Proceeding with application startup...'; exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
