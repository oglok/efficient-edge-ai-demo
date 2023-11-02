FROM nvcr.io/nvidia/l4t-ml:r35.2.1-py3 AS builder

RUN pip install --no-cache --no-deps ultralytics setuptools==59.5.0
RUN pip install --no-cache tqdm lapx matplotlib pandas psutil pyyaml scipy seaborn sentry-sdk thop numpy==1.23.5 protobuf==3.20.0 grpcio-tools  --upgrade
RUN pip install --no-cache setuptools==45.2.0
RUN pip install --no-cache futures

# Install grpcio-tools and compile protobuf protocols
COPY ./protobuf /protobuf
RUN cd /protobuf/ && python3 -m grpc_tools.protoc -I./ --python_out=. --pyi_out=. --grpc_python_out=. ./yoloserving.proto

RUN cd / && yolo export model=yolov8n.pt format=engine device=0

FROM nvcr.io/nvidia/l4t-base:35.4.1

# Install dependencies with apt/pip
ENV LD_LIBRARY_PATH=/usr/lib/llvm-8/lib:$LD_LIBRARY_PATH
RUN apt update && apt install -y gcc python3-dev python3-pip autoconf bc build-essential g++-8 gcc-8 clang-8 lld-8 gettext-base gfortran-8 iputils-ping libbz2-dev libc++-dev libcgal-dev libffi-dev libfreetype6-dev libhdf5-dev libjpeg-dev liblzma-dev libncurses5-dev libncursesw5-dev libpng-dev libreadline-dev libssl-dev libsqlite3-dev libxml2-dev libxslt-dev locales moreutils openssl python-openssl rsync scons python3-pip libopenblas-dev

ENV LD_LIBRARY_PATH=/usr/lib/llvm-8/lib:$LD_LIBRARY_PATH
RUN python3 -m pip install --no-cache setuptools==59.5.0
RUN python3 -m pip install --no-cache tqdm lapx matplotlib pandas psutil pyyaml scipy seaborn sentry-sdk thop grpcio aiohttp numpy==1.23.5 protobuf==3.20.0 https://developer.download.nvidia.cn/compute/redist/jp/v511/pytorch/torch-2.0.0+nv23.05-cp38-cp38-linux_aarch64.whl

RUN pip install --no-cache --no-deps ultralytics supervision setuptools==59.5.0
RUN pip install --no-cache setuptools==45.2.0
RUN pip install --no-cache futures

# Remove dependencies used only for local builds/installs
RUN apt remove gcc python3-dev  autoconf bc build-essential g++-8 gcc-8 clang-8 lld-8 gettext-base gfortran-8 iputils-ping libbz2-dev libc++-dev libcgal-dev libffi-dev libfreetype6-dev libhdf5-dev libjpeg-dev liblzma-dev libncurses5-dev libncursesw5-dev libpng-dev libreadline-dev libssl-dev libsqlite3-dev libxml2-dev libxslt-dev locales moreutils openssl python-openssl rsync scons libopenblas-dev -y && apt autoremove -y && apt clean

RUN apt install -y --no-install-recommends --no-install-suggests cuda-minimal-build-11-4 cuda-nvrtc-11-4 libcudnn8 libcublas-11-4 libcurand-11-4 nvidia-tensorrt

COPY ./yoloserver/ /opt/yoloserver
COPY --from=builder /protobuf/ /opt/yoloserver/
COPY --from=builder /yolov8n.engine /opt/yoloserver/yolov8n.engine

RUN find /usr/local/lib/python3.8/dist-packages -name '*.so' -exec strip {} \;

WORKDIR /opt/yoloserver

CMD python3 yoloserver.py
