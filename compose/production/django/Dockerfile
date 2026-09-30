ARG PYTHON_IMAGE_VER=3.12

FROM python:${PYTHON_IMAGE_VER}-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONUNBUFFERED 1
ENV PATH="/app/.venv/bin:$PATH"

RUN apt-get update \
  # dependencies for building Python packages and Docker healthcheck
  && apt-get install -y build-essential curl git\
  # psycopg2 dependencies
  && apt-get install -y libpq-dev \
  # Translations dependencies
  && apt-get install -y gettext \
  # cleaning up unused files
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

RUN addgroup --system django \
    && adduser --system --ingroup django django

# Install dependencies using uv workspace caching
WORKDIR /app
RUN --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=django/pyproject.toml,target=django/pyproject.toml \
    uv sync --frozen --no-dev --no-install-project --package scram-django

COPY --chown=django:django ./compose/production/django/entrypoint /entrypoint
RUN sed -i 's/\r$//g' /entrypoint
RUN chmod +x /entrypoint

COPY --chown=django:django ./compose/production/django/start /start
RUN sed -i 's/\r$//g' /start
RUN chmod +x /start

COPY --chown=django:django ./django /app

USER django

WORKDIR /app/src

ENTRYPOINT ["/entrypoint"]
