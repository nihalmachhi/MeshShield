FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MESHSHIELD_HOME=/app

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY frontend ./frontend
RUN python -m pip install --no-cache-dir . \
    && mkdir -p /app/data/generated \
    && groupadd --system meshshield \
    && useradd --system --gid meshshield --home-dir /app meshshield \
    && chown -R meshshield:meshshield /app/data

USER meshshield
EXPOSE 8000
CMD ["meshshield", "serve", "--host", "0.0.0.0", "--port", "8000"]
