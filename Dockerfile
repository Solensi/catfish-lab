FROM python:3.13-slim@sha256:9d2e5553305c7c7b0097999bb17187c69b921ccd6bc9d40e4bb5ebe652c00285

COPY --from=ghcr.io/astral-sh/uv:0.12.9@sha256:8b940d3a9d65bed080436972241af2e21c84b5e8c9193f7014ed71479ee795ff /uv /uvx /bin/

LABEL org.opencontainers.image.title="Catfish Lab"
LABEL org.opencontainers.image.description="Evidence-driven, multi-role development harness"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_NO_DEV=1 \
    PATH="/opt/catfish-lab/.venv/bin:$PATH"

WORKDIR /opt/catfish-lab

COPY pyproject.toml uv.lock README.md LICENSE ./
COPY lab ./lab

RUN uv sync --locked --extra docs --no-editable

WORKDIR /workspace
COPY mkdocs.yml README.md ./
COPY docs ./docs
RUN lab init

ENTRYPOINT ["lab"]
CMD ["--help"]
