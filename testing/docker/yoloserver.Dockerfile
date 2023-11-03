FROM nvcr.io/nvidia/l4t-ml:r35.2.1-py3 AS builder

# Install pip dependencies for build
RUN pip install --no-cache --no-deps ultralytics setuptools==59.5.0
RUN pip install --no-cache tqdm lapx matplotlib pandas psutil pyyaml scipy seaborn sentry-sdk thop numpy==1.23.5 protobuf==3.20.0 grpcio-tools  --upgrade
# setuptools has a bug requiring 59.5.0 for grpcio and 45.2.0 for futures
RUN pip install --no-cache setuptools==45.2.0
RUN pip install --no-cache futures

# Install grpcio-tools and compile protobuf protocols
COPY ./protobuf /protobuf
RUN cd /protobuf/ && python3 -m grpc_tools.protoc -I./ --python_out=. --pyi_out=. --grpc_python_out=. ./yoloserving.proto

# Compile TensorRT engine using YOLO model/package
RUN cd / && yolo export model=yolov8n.pt format=engine device=0

FROM nvcr.io/nvidia/l4t-base:35.4.1

# Install dependencies with apt/pip
ENV LD_LIBRARY_PATH=/usr/lib/llvm-8/lib:$LD_LIBRARY_PATH
RUN apt update && apt install -y gcc python3-dev python3-pip autoconf bc build-essential g++-8 gcc-8 clang-8 lld-8 gettext-base gfortran-8 iputils-ping libbz2-dev libc++-dev libcgal-dev libffi-dev libfreetype6-dev libhdf5-dev libjpeg-dev liblzma-dev libncurses5-dev libncursesw5-dev libpng-dev libreadline-dev libssl-dev libsqlite3-dev libxml2-dev libxslt-dev locales moreutils openssl python-openssl rsync scons python3-pip libopenblas-dev wget git
ENV LD_LIBRARY_PATH=/usr/lib/llvm-8/lib:$LD_LIBRARY_PATH
RUN python3 -m pip install --no-cache setuptools==59.5.0
RUN python3 -m pip install --no-cache tqdm lapx ninja matplotlib pandas psutil pyyaml scipy seaborn sentry-sdk thop grpcio aiohttp numpy==1.23.5 protobuf==3.20.0 https://developer.download.nvidia.cn/compute/redist/jp/v511/pytorch/torch-2.0.0+nv23.05-cp38-cp38-linux_aarch64.whl
RUN python3 -m pip install --no-cache --no-deps ultralytics supervision setuptools==59.5.0
RUN python3 -m pip install --no-cache setuptools==45.2.0
RUN python3 -m pip install --no-cache futures requests

RUN apt install -y nvidia-cuda nvidia-cuda-dev 

RUN git clone --branch release/0.15 https://github.com/pytorch/vision.git

RUN apt install -y libcudnn8 libcublas-11-4 python3-libnvinfer libcufft-11-4 cuda-toolkit-11-4

RUN cd vision && BUILD_VERSION=0.15.1 CUDA_VISIBLE_DEVICES=0 python3 setup.py install --user

RUN rm -rf /vision
RUN mkdir /opt/yoloserver/
RUN wget -O /opt/yoloserver/image.jpg https://media.npr.org/assets/img/2013/06/04/ducky062way-4bd453a4ade1d0f971e97598b78a44b5cc7b760a-s1100-c50.jpg

# Upgrade all OS files
RUN apt upgrade -y

# Remove dependencies used only for local builds/installs
RUN python3 -m pip uninstall -y ninja setuptools
RUN apt remove -y gcc python3-dev  autoconf bc build-essential g++-8 gcc-8 clang-8 lld-8 gettext-base gfortran-8 iputils-ping libbz2-dev libc++-dev libcgal-dev libffi-dev libfreetype6-dev libhdf5-dev libjpeg-dev liblzma-dev libncurses5-dev libncursesw5-dev libpng-dev libreadline-dev libssl-dev libsqlite3-dev libxml2-dev libxslt-dev locales moreutils openssl python-openssl rsync scons libopenblas-dev wget git nvidia-cuda nvidia-cuda-dev && apt autoremove -y && apt clean


# Add the CUDA components required for serving
RUN apt install -y --no-install-recommends --no-install-suggests cuda-minimal-build-11-4 cuda-nvrtc-11-4 libcudnn8 libcublas-11-4 libcurand-11-4 nvidia-tensorrt libopencv-python python3-libnvinfer libcufft-11-4 cuda-toolkit-11-4

# Copy the yoloserver, TensorRT engine, and protobuf protocol to our image
COPY ./yoloserver/ /opt/yoloserver
COPY --from=builder /protobuf/ /opt/yoloserver/
COPY --from=builder /yolov8n.engine /opt/yoloserver/yolov8n.engine

# Strip libraries of debug symbols (grpcio is the worst offender in this image)
RUN find /usr/local/lib/python3.8/dist-packages -name '*.so' -exec strip {} \;

# Set container params
WORKDIR /opt/yoloserver
CMD python3 yoloserver.py
