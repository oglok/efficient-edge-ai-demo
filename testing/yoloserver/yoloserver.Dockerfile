FROM nvcr.io/nvidia/l4t-pytorch:r35.2.1-pth2.0-py3 AS builder

RUN pip install --no-deps ultralytics
RUN pip install tqdm lapx matplotlib pandas psutil pyyaml scipy seaborn sentry-sdk thop numpy==1.23.5 protobuf==3.20.0 futures grpcio-tools  --upgrade

COPY ./protobuf /protobuf

RUN cd /protobuf/ && python -m grpc_tools.protoc -I./ --python_out=. --pyi_out=. --grpc_python_out=. ./yoloserving.proto

RUN cd / && yolo export model=yolov8n.pt format=engine device=0

FROM nvcr.io/nvidia/l4t-pytorch:r35.2.1-pth2.0-py3

RUN pip install --no-deps ultralytics supervision
RUN pip install tqdm lapx matplotlib pandas psutil pyyaml scipy seaborn sentry-sdk thop numpy==1.23.5 protobuf==3.20.0 futures --upgrade

RUN mkdir -p /app/
COPY ./ /opt/yoloserver
COPY --from=builder /protobuf /opt/yoloserver/
COPY --from=builder /yolov8n.engine /opt/yoloserver/yolov8n.engine

WORKDIR /opt/yoloserver

CMD python3 yoloserver.py
