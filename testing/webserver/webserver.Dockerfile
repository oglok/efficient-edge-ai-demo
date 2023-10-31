FROM docker.io/ubuntu:20.04

RUN pip3 install flask setuptools==56.5.0 grpcio

COPY ./app /app/

WORKDIR /app

ENV FLASK_APP=server
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
CMD python3 -m flask run --host 0.0.0.0
