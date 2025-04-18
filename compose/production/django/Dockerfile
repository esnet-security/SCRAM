ARG PYTHON_IMAGE_VER=3.12


FROM python:${PYTHON_IMAGE_VER}-slim-bookworm


ENV PYTHONUNBUFFERED 1

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

# Requirements are installed here to ensure they will be cached.
COPY ./requirements/ /requirements
RUN pip install uv
RUN uv pip install --system --no-cache-dir -r /requirements/production.txt \
    && rm -rf /requirements

COPY --chown=django:django ./compose/production/django/entrypoint /entrypoint
RUN sed -i 's/\r$//g' /entrypoint
RUN chmod +x /entrypoint

COPY --chown=django:django ./compose/production/django/start /start
RUN sed -i 's/\r$//g' /start
RUN chmod +x /start

COPY --chown=django:django . /app

USER django

WORKDIR /app

ENTRYPOINT ["/entrypoint"]
