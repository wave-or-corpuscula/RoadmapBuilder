FROM python:3.12-slim

WORKDIR /workspace

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/workspace

COPY requirements.txt /workspace/backend/requirements.txt
RUN pip install --no-cache-dir -r /workspace/backend/requirements.txt

COPY . /workspace/backend

EXPOSE 8000

CMD ["sh", "-c", "cd /workspace/backend && alembic upgrade head && uvicorn backend.main:app --host 0.0.0.0 --port 8000"]
