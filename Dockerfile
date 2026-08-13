FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY config ./config
RUN python -m pip install --upgrade pip && python -m pip install .

EXPOSE 8080
CMD ["uvicorn", "paymind.api.app:app", "--host", "0.0.0.0", "--port", "8080"]
