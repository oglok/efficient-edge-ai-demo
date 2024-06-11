# FROM nvcr.io/nvidia/l4t-ml:r36.2.0-py3 AS builder

# # Install pip dependencies for build
# RUN pip install --no-cache --no-deps ultralytics setuptools tqdm lapx matplotlib grpcio-tools

# # Install grpcio-tools and compile protobuf protocols
# COPY ./protobuf /protobuf
# RUN cd /protobuf/ && python3 -m grpc_tools.protoc -I./ --python_out=. --pyi_out=. --grpc_python_out=. ./yoloserving.proto

# # Compile TensorRT engine using YOLO model/package
# RUN cd / && yolo export model=yolov8n.pt format=engine device=0

FROM nvcr.io/nvidia/l4t-ml:r36.2.0-py3

COPY yoloserver/ /opt/yoloserver/
COPY yolov8n.pt /opt/yoloserver/
COPY protobuf/* /opt/yoloserver/

#COPY --from=builder /protobuf/ /opt/yoloserver/
#COPY --from=builder /yolov8n.engine /opt/yoloserver/yolov8n.engine

RUN pip install ultralytics
RUN pip install supervision
RUN pip install --no-cache tqdm lapx ninja matplotlib pandas psutil pyyaml scipy seaborn sentry-sdk thop grpcio aiohttp
RUN pip install --upgrade grpcio

RUN apt update
RUN apt install -y libc++-dev libcgal-dev libffi-dev libfreetype6-dev libhdf5-dev libjpeg-dev liblzma-dev libncurses5-dev libncursesw5-dev libpng-dev libreadline-dev libssl-dev libsqlite3-dev libxml2-dev libxslt-dev libbz2-dev

WORKDIR /opt/yoloserver

CMD python3 yoloserver.py
