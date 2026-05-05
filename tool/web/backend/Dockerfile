FROM python:3.12-slim

WORKDIR /app

# Backend code only; data volume mounts at /app/data
COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY . .

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
