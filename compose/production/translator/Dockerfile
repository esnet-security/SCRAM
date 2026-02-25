FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

ENV PYTHONUNBUFFERED=1
ENV UV_NO_DEV=1

RUN apt-get update \
  # dependencies for building Python packages
  && apt-get install -y build-essential git \
  # cleaning up unused files
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY ./translator/pyproject.toml ./translator/uv.lock* ./

# Install deps only (as protobuf stuff doesn't exist yet but we need deps to setup protobufs)
RUN uv sync --locked --no-install-project

# put the venv into PATH
ENV PATH="/app/.venv/bin:$PATH"

COPY ./translator/src /app/

# Generate protobuf files
# TODO: Make this less jank and don't do the git clone crap?
# Protos don't work well in packages so we generate them in /app/ outside the package so that bare
# `import gobgp_pb2` style imports work.
RUN git clone -b v3.33.0 https://github.com/osrg/gobgp.git gobgp \
    && cd gobgp/api \
    && python3 -m grpc_tools.protoc -I./ \
    --python_out=/app/ \
    --pyi_out=/app/ \
    --grpc_python_out=/app/ \
    *.proto \
    && cd /app && rm -rf gobgp

# Install the project itself (including the protobuff stuff)
RUN uv sync --locked

ENTRYPOINT ["python", "-m", "translator.translator"]
