# Start builder image build
FROM docker.io/dustynv/mlc:r36.2.0 AS builder

# Install and enable git-lfs
RUN apt-get update && apt-get install git-lfs
RUN git lfs install

# Clone local copy of Vicuna-7b-v1.5
RUN mkdir /opt/models
RUN cd /opt/models && git clone https://huggingface.co/lmsys/vicuna-7b-v1.5

# Install grpcio-tools and compile protobuf protocols
RUN pip install grpcio-tools
COPY ./protobuf /protobuf
RUN cd /protobuf/ && python3 -m grpc_tools.protoc -I./ --python_out=. --pyi_out=. --grpc_python_out=. ./vicunaserving.proto

# Compile vicuna-7b-v1.5
RUN python3 -m mlc_llm.build \
    --model vicuna-7b-v1.5 \
    --quantization q4f16_ft \
    --artifact-path /opt/ \
    --max-seq-len 4096 \
    --target cuda

### End builder image build ###
FROM nvcr.io/nvidia/l4t-base:r36.2.0

COPY ./vicunaserver/ /opt/vicunaserver/
COPY --from=builder /opt/vicuna-7b-v1.5-q4f16_ft/ /opt/vicunaserver/
COPY --from=builder /opt/mlc_llm-0.1.dev930+g607dc5a-py3-none-any.whl /tmp
COPY --from=builder /opt/torch-2.1.0-cp310-cp310-linux_aarch64.whl /tmp
COPY --from=builder /opt/torchvision-0.16.0+fbb4cc5-cp310-cp310-linux_aarch64.whl /tmp
COPY --from=builder /opt/mlc_chat-0.1.dev930+g607dc5a-cp310-cp310-linux_aarch64.whl /tmp
COPY --from=builder /opt/tvm-0.15.dev48+g59c355604-cp310-cp310-linux_aarch64.whl /tmp

# Install dependencies with apt/pip
#RUN apt update && apt install -y gcc python3-dev python3-pip autoconf bc build-essential g++ gcc clang lld gettext-base gfortran iputils-ping libbz2-dev libc++-dev libcgal-dev libffi-dev libfreetype6-dev libhdf5-dev libjpeg-dev liblzma-dev libncurses5-dev libncursesw5-dev libpng-dev libreadline-dev libssl-dev libsqlite3-dev libxml2-dev libxslt-dev locales moreutils openssl python3-openssl rsync scons python3-pip libopenblas-dev

RUN apt update && apt install -y python3-pip libbz2-dev libc++-dev libcgal-dev libffi-dev libfreetype6-dev libhdf5-dev libjpeg-dev liblzma-dev libncurses5-dev libncursesw5-dev libpng-dev libreadline-dev libssl-dev libsqlite3-dev libxml2-dev libxslt-dev

RUN python3.10 -m pip install setuptools
RUN python3.10 -m pip install /tmp/*.whl grpcio grpcio-tools

# Install essential CUDA packages
RUN apt-cache search cuda-*
RUN apt install -y cuda-minimal-build-12-2 cuda-nvrtc-12-2 libcudnn8 libcublas-12-2 libcurand-12-2

# Copy protobuf defs
COPY --from=builder /protobuf/ /opt/vicunaserver

# Strip the libs -- grpcio and the mlc-llm built TVM/cutlass kernel libraries are the worst offenders -- multi GiB space savings
RUN find /usr/local/lib/python3.10/dist-packages -name '*.so' -exec strip {} \;

# Set workdir to where our server is
WORKDIR /opt/vicunaserver/

ENV LD_LIBRARY_PATH=/usr/local/lib/python3.10/dist-packages/tvm/:/usr/local/lib:$LD_LIBRARY_PATH

# Set default CMD to run our server
CMD python3 vicunaserver.py
