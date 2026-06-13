FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project   # deps first (better layer caching)
COPY src ./src
RUN uv sync --frozen --no-dev
# 8000 keeps Cloud Run AND Azure happy; see deploy step
ENV PORT=8000
EXPOSE 8000
CMD ["uv", "run", "carbon-mcp"]