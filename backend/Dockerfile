FROM python:3.11-slim

WORKDIR /code

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY data ./data

EXPOSE 8000

# Ollama runs on the host machine. On Docker Desktop (Windows/macOS) use:
#   docker run -p 8000:8000 -e OLLAMA_HOST=http://host.docker.internal:11434 rag-backend
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
