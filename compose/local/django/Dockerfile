ARG PYTHON_IMAGE_VER=3.12

FROM python:${PYTHON_IMAGE_VER}-slim-bookworm

ENV PIP_ROOT_USER_ACTION ignore
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN apt-get update \
  # dependencies for building Python packages and Docker healthcheck
  && apt-get install -y build-essential curl git \
  # psycopg2 dependencies
  && apt-get install -y libpq-dev \
  # Translations dependencies
  && apt-get install -y gettext \
  # cleaning up unused files
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

# Requirements are installed here to ensure they will be cached.
COPY ./django/requirements /requirements
RUN pip install uv
RUN uv pip install --system -r /requirements/local.txt --prerelease=allow

COPY ./compose/production/django/entrypoint /entrypoint
RUN sed -i 's/\r$//g' /entrypoint
RUN chmod +x /entrypoint

COPY ./compose/local/django/start /start
RUN sed -i 's/\r$//g' /start
RUN chmod +x /start

ENV PATH="$PATH:/app/src"
WORKDIR /app/src

ENTRYPOINT ["/entrypoint"]
