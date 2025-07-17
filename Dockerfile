FROM python:3.10-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy the app source code
COPY . /app
WORKDIR /app

# Create virtual environment and install dependencies
RUN uv venv --python 3.10 --no-cache
RUN uv sync --frozen --no-cache

# Expose the app port
EXPOSE 8001

# Set environment variables
ENV HOST=0.0.0.0
ENV PORT=8001

# Run Alembic migrations and start the FastAPI app using uv
CMD ["/bin/sh", "-c", "uv run alembic upgrade head && uv run uvicorn app.main:app --host $HOST --port $PORT"]

