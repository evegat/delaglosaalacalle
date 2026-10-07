FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src:/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY dist/ dist/
COPY data/ data/

# La API necesita escribir SQLite en /app/data; el proceso no requiere root.
RUN useradd --system --uid 10001 --create-home appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8088

CMD ["uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "8088"]
