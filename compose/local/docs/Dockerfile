ARG PYTHON_IMAGE_VER=3.12

FROM python:${PYTHON_IMAGE_VER}-slim-bookworm

ENV PIP_ROOT_USER_ACTION ignore
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN apt-get update \
    # dependencies for building Python packages
    && apt-get install -y build-essential git \
    # psycopg2 dependencies
    && apt-get install -y libpq-dev \
    # Translations dependencies
    && apt-get install -y gettext \
    # Uncomment below lines to enable Sphinx output to latex and pdf
    # && apt-get install -y texlive-latex-recommended \
    # && apt-get install -y texlive-fonts-recommended \
    # && apt-get install -y texlive-latex-extra \
    # && apt-get install -y latexmk \
    # cleaning up unused files
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && rm -rf /var/lib/apt/lists/*


# Only re-run the pip install if these files have changed
COPY requirements/base.txt requirements/local.txt requirements/production.txt /app/requirements/
RUN pip install uv
RUN uv pip install -r /app/requirements/local.txt -r /app/requirements/production.txt

COPY . /app/

WORKDIR /app
