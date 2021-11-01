FROM python:3.8-slim-buster

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN apt-get update \
  # dependencies for building Python packages
  && apt-get install -y build-essential git \
  # cleaning up unused files
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

# Requirements are installed here to ensure they will be cached.
COPY ./translator/requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

RUN mkdir /app \
    && cd /app \
    && git clone https://github.com/osrg/gobgp.git \
    && cd gobgp/api \
    && python3 -m grpc_tools.protoc -I./ --python_out=/app/ --grpc_python_out=/app/ *.proto

COPY ./translator/add_path.py /app
COPY ./translator/tests /app
RUN chmod +x /app/add_path.py

WORKDIR /app

ENTRYPOINT ["/app/add_path.py"]
