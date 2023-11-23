# Start builder image build
FROM docker.io/dustynv/mlc:r35.4.1 AS builder

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

# Patch param_manager with commit (non-functional without): https://github.com/mlc-ai/mlc-llm/commit/4fc6afba4046bc37d3241c6d3d06b12a021cf00f
RUN wget -O /usr/local/lib/python3.8/dist-packages/mlc_llm/relax_model/param_manager.py https://raw.githubusercontent.com/mlc-ai/mlc-llm/4fc6afba4046bc37d3241c6d3d06b12a021cf00f/mlc_llm/relax_model/param_manager.py

# Compile vicuna-7b-v1.5
RUN python3 -m mlc_llm.build \
    --model vicuna-7b-v1.5 \
    --quantization q4f16_ft \
    --artifact-path /opt/ \
    --max-seq-len 4096 \
    --target cuda

### End builder image build ###

# Start main image build
FROM nvcr.io/nvidia/l4t-base:35.4.1

# Copy vicunaserver,  compiled model, and whl files for pip install
COPY ./vicunaserver/ /opt/vicunaserver/
COPY --from=builder /opt/vicuna-7b-v1.5-q4f16_ft/ /opt/vicunaserver/
COPY --from=builder /opt/mlc_chat-0.0.0-cp38-cp38-linux_aarch64.whl /tmp
COPY --from=builder /opt/tvm-0.12.dev1610+gceaf7b015-cp38-cp38-linux_aarch64.whl /tmp

# Install dependencies with apt/pip
RUN apt update && apt install -y gcc python3-dev python3-pip autoconf bc build-essential g++-8 gcc-8 clang-8 lld-8 gettext-base gfortran-8 iputils-ping libbz2-dev libc++-dev libcgal-dev libffi-dev libfreetype6-dev libhdf5-dev libjpeg-dev liblzma-dev libncurses5-dev libncursesw5-dev libpng-dev libreadline-dev libssl-dev libsqlite3-dev libxml2-dev libxslt-dev locales moreutils openssl python-openssl rsync scons python3-pip libopenblas-dev
ENV LD_LIBRARY_PATH=/usr/lib/llvm-8/lib:$LD_LIBRARY_PATH
RUN python3.8 -m pip install --no-cache setuptools==59.5.0
RUN python3.8 -m pip install --no-cache /tmp/*.whl grpcio aiohttp numpy==1.23.5 scipy=='1.5.3' protobuf https://developer.download.nvidia.cn/compute/redist/jp/v511/pytorch/torch-2.0.0+nv23.05-cp38-cp38-linux_aarch64.whl

# Patch mlc_chat with stream iterator commit: https://github.com/mlc-ai/mlc-llm/commit/830656fa9779ecfb121b7eef218d04e1ad7e50bf
RUN apt install wget -y
RUN wget -O /usr/local/lib/python3.8/dist-packages/mlc_chat/callback.py https://raw.githubusercontent.com/mlc-ai/mlc-llm/830656fa9779ecfb121b7eef218d04e1ad7e50bf/python/mlc_chat/callback.py

RUN apt upgrade -y

# Remove dependencies used only for local builds/installs
RUN pip uninstall scipy sympy networkx pydantic aiohttp setuptools tornado pydantic_core -y
RUN apt remove wget python-setuptools gcc python3-dev  autoconf bc build-essential g++-8 gcc-8 clang-8 lld-8 gettext-base gfortran-8 iputils-ping libbz2-dev libc++-dev libcgal-dev libffi-dev libfreetype6-dev libhdf5-dev libjpeg-dev liblzma-dev libncurses5-dev libncursesw5-dev libpng-dev libreadline-dev libssl-dev libsqlite3-dev libxml2-dev libxslt-dev locales moreutils openssl python-openssl rsync scons python3-pip libopenblas-dev -y && apt autoremove -y && apt clean

# Install essential CUDA packages
RUN apt install -y --no-install-recommends --no-install-suggests cuda-minimal-build-11-4 cuda-nvrtc-11-4 libcudnn8 libcublas-11-4 libcurand-11-4

# Copy protobuf defs
COPY --from=builder /protobuf/ /opt/vicunaserver

# Copy cutlass kernel for mlc-llm
#COPY --from=builder /opt/mlc-llm/build/libmlc_llm.so /opt/mlc-llm/build/libmlc_llm.so
#COPY --from=builder /opt/mlc-llm/build/libmlc_llm_module.so /opt/mlc-llm/build/libmlc_llm_module.so
#COPY --from=builder /opt/mlc-llm/build/tvm/libtvm.so /opt/mlc-llm/build/tvm/libtvm.so
#COPY --from=builder /opt/mlc-llm/build/tvm/libtvm_runtime.so /opt/mlc-llm/build/tvm/libtvm_runtime.so
COPY --from=builder /opt/mlc-llm/build/tvm/3rdparty/cutlass_fpA_intB_gemm/cutlass_kernels/libfpA_intB_gemm.so /opt/mlc-llm/build/tvm/3rdparty/cutlass_fpA_intB_gemm/cutlass_kernels/libfpA_intB_gemm.so

# Strip the libs -- grpcio and the mlc-llm built TVM/cutlass kernel libraries are the worst offenders -- multi GiB space savings
RUN find /usr/local/lib/python3.8/dist-packages -name '*.so' -exec strip {} \;
RUN strip /opt/mlc-llm/build/tvm/3rdparty/cutlass_fpA_intB_gemm/cutlass_kernels/libfpA_intB_gemm.so

# Set workdir to where our server is
WORKDIR /opt/vicunaserver/

# Set default CMD to run our server
CMD python3 vicunaserver.py
