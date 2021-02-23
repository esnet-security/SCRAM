FROM python:slim-buster
ENV PYTHONUNBUFFERED=1
WORKDIR /code

RUN apt-get update -qy
RUN apt-get install -y python3-dev python3-pip
COPY . /code/

RUN pip install -r requirements-dev.txt

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]