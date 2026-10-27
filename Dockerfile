FROM python:3.12.3-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN useradd --create-home appuser \
    && mkdir /app/results \
    && chown appuser:appuser /app/results

COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser prompts/ ./prompts/

USER appuser

ENTRYPOINT ["python", "src/inference.py"]