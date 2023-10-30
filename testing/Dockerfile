FROM docker.io/dustynv/mlc:r35.4.1 as mlc-builder

RUN apt-get update && apt-get install git-lfs

RUN git lfs install

RUN mkdir /opt/models && cd /opt/models && git clone https://huggingface.co/lmsys/vicuna-7b-v1.5

RUN python3 -m mlc_llm.build \
    --model vicuna-7b-v1.5 \
    --quantization q4f16_ft \
    --artifact-path /opt/ \
    --max-seq-len 4096 \
    --target cuda \

FROM nvcr.io/nvidia/l4t-pytorch:r35.2.1-pth2.0-py3

RUN apt-get update

RUN pip3 install flask
RUN pip install --no-deps ultralytics supervision
RUN pip install tqdm lapx matplotlib pandas psutil pyyaml scipy seaborn sentry-sdk thop numpy==1.23.5 protobuf==3.20.0 futures py-cpuinfo --upgrade
RUN apt-get install libgstrtspserver-1.0-0 libgstreamer-plugins-bad1.0-dev- -y
RUN apt install gir1.2-gst-rtsp-server-1.0 vim -y

COPY ./mlc_chat-0.0.0-cp38-cp38-linux_aarch64.whl /tmp
COPY ./tvm-0.12.dev1610+gceaf7b015-cp38-cp38-linux_aarch64.whl /tmp
RUN pip install /tmp/*.whl
RUN rm -rf /tmp/*.whl

COPY --from=mlc-builder /opt/mlc-llm /opt/
RUN mkdir -p /app/storage
COPY --from=mlc-builder /opt/vicuna-7b-v1.5-q4f16_ft/ /app/storage

RUN cd /app/storage && yolo export model=yolov8n.pt format=engine device=0
RUN rm -rf /app/storage/yolov8n.pt

COPY ./callback.py /usr/local/lib/python3.8/dist-packages/mlc_chat/callback.py
COPY ./param_manager.py /usr/local/lib/python3.8/dist-packages/mlc_llm/relax_model/param.manager.py
RUN update-alternatives --install /usr/local/bin/python python \
/usr/bin/python3.8 3

RUN mkdir /app/

WORKDIR /app/storage

ENV TVM_HOME=/opt/mlc-llm/3rdparty/tvm
ENV FLASK_APP=server
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
CMD python3 -m flask run --host 0.0.0.0
