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
COPY ./translator/requirements /requirements
RUN pip install -r /requirements/base.txt

RUN mkdir /app \
  && cd /app \
  && git clone https://github.com/Tuetuopay/gobgp.git \
  && cd gobgp \
  && git checkout 11d7cf1feec458867cbea8d52e594f5bcd889b04 \
  && cd api \
  && python3 -m grpc_tools.protoc -I./ --python_out=/app/ --pyi_out=/app/ --grpc_python_out=/app/ *.proto

COPY ./translator/translator.py /app
COPY ./translator/gobgp.py /app
COPY ./translator/exceptions.py /app
COPY ./translator/shared.py /app

RUN chmod +x /app/translator.py

WORKDIR /app

ENTRYPOINT ["/app/translator.py"]
