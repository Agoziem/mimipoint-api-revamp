FROM python:3.10-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy the application into the container.
COPY . /app

# Install the application dependencies.
WORKDIR /app

RUN uv venv --python 3.10 --no-cache
RUN uv sync --frozen --no-cache

# Expose the port
EXPOSE 8000

# Set environment variables
ENV HOST=0.0.0.0
ENV PORT=8000

# # Run the FastAPI application
CMD ["/app/.venv/bin/uvicorn","app.main:app", "--host", "0.0.0.0", "--port", "8000"]
