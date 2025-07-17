FROM python:3.10-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY . /app
WORKDIR /app

RUN uv venv --python 3.10 --no-cache
RUN uv sync --frozen --no-cache

EXPOSE 8000

ENV HOST=0.0.0.0
ENV PORT=8000

CMD ["/bin/sh", "-c", "/app/.venv/bin/alembic upgrade head && /app/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000"]


