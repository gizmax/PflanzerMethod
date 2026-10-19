FROM python:3.12-slim

# Mirror the repo layout (/app = repo root) so that:
#   - backend is importable as a package (main.py uses relative imports)
#   - models.REPO_ROOT (parents[3]) resolves to /app → DB at /app/data (volume)
WORKDIR /app/tool/web/backend

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY . .

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--app-dir", "/app/tool/web", "--host", "0.0.0.0", "--port", "8000"]
