FROM python:3.9.18-slim-bullseye as builder

RUN pip install grpcio-tools

COPY ./protobuf /protobuf

RUN cd /protobuf/ && python -m grpc_tools.protoc -I./ --python_out=. --pyi_out=. --grpc_python_out=. ./yoloserving.proto
RUN cd /protobuf/ && python -m grpc_tools.protoc -I./ --python_out=. --pyi_out=. --grpc_python_out=. ./vicunaserving.proto

RUN apt-get update && apt-get install curl -y

RUN mkdir /redis && cd /redis && curl -Lo redis.tgz https://packages.redis.io/redis-stack/redis-stack-server-7.2.0-v5.focal.arm64.tar.gz?_gl=1*5g9e47*_ga*MTI0NDQ4ODI3LjE2OTg3MDgwMjU.*_ga_8BKGRQKRPV*MTY5ODgwNDczOS40LjAuMTY5ODgwNDc0MC41OS4wLjA.*_gcl_au*ODM2ODgwMzg4LjE2OTg3MDgwMjQ.

RUN cd /redis && tar -xzf redis.tgz

FROM python:3.9.18-slim-bullseye

RUN pip install flask setuptools==59.5.0 grpcio redis protobuf

COPY ./webserver /opt/webserver/
COPY --from=builder /protobuf/ /opt/webserver
COPY --from=builder /redis/redis-stack-server-7.2.0-v5/ /opt/redis/

WORKDIR /opt/webserver

ENV FLASK_APP=webserver
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
CMD /opt/redis/bin/redis-server & python3 -m flask run --host 0.0.0.0
