FROM ghcr.io/astral-sh/uv:0.7.6 AS uv
FROM python:3.12-slim-bookworm
COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy \
    PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" CONTROL_TOWER_ROOT=/app
RUN useradd --create-home --uid 10001 app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --extra lesson03 --no-dev --no-install-project
COPY src ./src
COPY data ./data
COPY incidents ./incidents
RUN uv sync --locked --extra lesson03 --no-dev && chown -R app:app /app
USER app
CMD ["python", "-m", "control_tower.runtime", "api"]
