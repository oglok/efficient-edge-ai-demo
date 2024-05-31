FROM nvcr.io/nvidia/l4t-ml:r36.2.0-py3

COPY yoloserver/ /opt/yoloserver/
COPY artifacts/* /opt/yoloserver/
RUN pip install ultralytics
RUN pip install supervision
RUN pip install --no-cache tqdm lapx ninja matplotlib pandas psutil pyyaml scipy seaborn sentry-sdk thop grpcio aiohttp
RUN pip install --upgrade grpcio

RUN apt update
RUN apt install -y libc++-dev libcgal-dev libffi-dev libfreetype6-dev libhdf5-dev libjpeg-dev liblzma-dev libncurses5-dev libncursesw5-dev libpng-dev libreadline-dev libssl-dev libsqlite3-dev libxml2-dev libxslt-dev libbz2-dev

WORKDIR /opt/yoloserver

CMD python3 yoloserver.py
