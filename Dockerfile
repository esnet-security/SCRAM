FROM python:slim-buster
ENV PYTHONUNBUFFERED=1
WORKDIR /code

RUN apt-get update &&  apt-get install -y \
    python3-dev \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-dev.txt .

RUN pip install -r requirements-dev.txt

COPY . /code/

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]