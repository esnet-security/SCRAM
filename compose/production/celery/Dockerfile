# Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

# Setup a non-root user
RUN groupadd --system --gid 999 nonroot \
    && useradd --system --gid 999 --uid 999 --create-home nonroot

# Install the project into `/app`
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Omit development dependencies
ENV UV_NO_DEV=1

# Ensure installed tools can be executed out of the box
ENV UV_TOOL_BIN_DIR=/usr/local/bin

COPY ./scheduler/pyproject.toml ./scheduler/uv.lock* ./
# Install the project's dependencies only
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=scheduler/pyproject.toml,target=scheduler/pyproject.toml \
    uv sync --frozen --no-install-project --package scheduler

# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching. We use --frozen since we
# have differing python versions across the stack.
COPY ./scheduler/src ./scheduler/src/

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=scheduler/pyproject.toml,target=scheduler/pyproject.toml \
    uv sync --frozen --package scheduler

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []

RUN chown -R nonroot:nonroot /app
USER nonroot

CMD ["celery", "-A", "scheduler.app:scram_api_scheduler", "worker", "--loglevel=info", "-E"]
