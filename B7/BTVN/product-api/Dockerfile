# ─── stage 1: builder ───
FROM python:3.12-slim AS builder
WORKDIR /build
COPY pyproject.toml ./
COPY src ./src
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir .

# ─── stage 2: runtime ───
FROM python:3.12-slim
WORKDIR /app
RUN groupadd -r app && useradd -r -g app -d /app app \
    && chown app:app /app

COPY --from=builder /opt/venv /opt/venv
COPY --chown=app:app migrations ./migrations
COPY --chown=app:app gunicorn.conf.py entrypoint.sh ./

ENV PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1

USER app
EXPOSE 5000
ENTRYPOINT ["sh", "./entrypoint.sh"]
