# Stage 1: Builder
FROM python:3.13 AS builder

WORKDIR /app

# Install uv
RUN pip install uv

# Copy dependency files first
COPY pyproject.toml uv.lock ./

# Install dependencies into the virtual environment
RUN UV_HTTP_TIMEOUT=600 UV_HTTP_RETRIES=10 uv sync --frozen --no-dev --no-install-project

# Stage 2: Runtime
FROM python:3.13-slim AS runtime

WORKDIR /app

# Copy the virtual environment built in Stage 1
COPY --from=builder /app/.venv /app/.venv

# Copy application source code
COPY src/ ./src/

# Use executables from the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "src.food11.serve:app", "--host", "0.0.0.0", "--port", "8000"]