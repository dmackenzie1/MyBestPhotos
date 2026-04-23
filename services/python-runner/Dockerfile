# Stage 1: Install CUDA deps — cached by Docker layer
FROM ghcr.io/astral-sh/uv:python3.12-bookworm AS builder
WORKDIR /workspace
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --project . --extra cuda-linux && \
    rm -rf /root/.cache/uv

# Stage 2: Final image — code mounted at runtime
FROM ghcr.io/astral-sh/uv:python3.12-bookworm
WORKDIR /workspace
ENV UV_LINK_MODE=copy
VOLUME ["/photos/library", "/data/cache"]
COPY --from=builder /workspace/.venv /.venv
