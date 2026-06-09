FROM python:3.12-slim

WORKDIR /app

# curl: usado por el healthcheck de Docker y disponible para depurar
# desde dentro del contenedor (docker exec bdns_api curl http://...).
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]