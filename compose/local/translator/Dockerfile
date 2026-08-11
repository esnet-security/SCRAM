FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

ENV PYTHONUNBUFFERED=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

RUN apt-get update \
  # dependencies for building Python packages
  && apt-get install -y build-essential git \
  # cleaning up unused files
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# At first we install  the deps only (as protobuf stuff doesn't exist yet but we need deps to setup protobufs). We also
# mount instead of copying to have a small build cache gain. Not that useful but is modern practice so why not.
RUN --mount=type=cache,target=/root/.cache/uv \
  --mount=type=bind,source=uv.lock,target=uv.lock \
  --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
  --mount=type=bind,source=translator/pyproject.toml,target=translator/pyproject.toml \
  uv sync --frozen --no-install-project --package translator

# put the venv into PATH
ENV PATH="/app/.venv/bin:$PATH"

COPY ./translator/src ./translator/src/

# Generate protobuf files
# TODO: Make this less jank and don't do the git clone crap?
# GoBGP v4 organizes its protos under proto/api/ and the protos import each other
# via "api/*.proto", so we compile from the proto/ root. That generates an `api`
# Python package under /app/, which we then import as `from api import gobgp_pb2`.
ARG GOBGP_VERSION=v4.8.0
RUN git clone -b ${GOBGP_VERSION} https://github.com/osrg/gobgp.git gobgp \
  && cd gobgp/proto \
  && python3 -m grpc_tools.protoc -I./ \
  --python_out=/app/ \
  --pyi_out=/app/ \
  --grpc_python_out=/app/ \
  api/*.proto \
  && touch /app/api/__init__.py \
  && cd /app && rm -rf gobgp

# Install the project itself (including the protobuff stuff) again mounting in the project files.
RUN --mount=type=cache,target=/root/.cache/uv \
  --mount=type=bind,source=uv.lock,target=uv.lock \
  --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
  --mount=type=bind,source=translator/pyproject.toml,target=translator/pyproject.toml \
  uv sync --frozen --package translator

ENTRYPOINT ["python", "-m", "translator.translator"]
