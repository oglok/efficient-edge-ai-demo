FROM nvcr.io/nvidia/l4t-pytorch:r35.2.1-pth2.0-py3
RUN apt-get update

RUN pip3 install flask
RUN pip install --no-deps ultralytics
RUN pip install tqdm lapx matplotlib pandas psutil pyyaml scipy seaborn sentry-sdk thop numpy protobuf==3.20.0 futures py-cpuinfo --upgrade
RUN apt-get install libgstrtspserver-1.0-0 libgstreamer-plugins-bad1.0-dev- -y
RUN apt install gir1.2-gst-rtsp-server-1.0 vim -y
RUN update-alternatives --install /usr/local/bin/python python \
/usr/bin/python3.8 3

WORKDIR /app

COPY *.py *.pt /app
ENV FLASK_APP=server
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
CMD python3 -m flask run --host 0.0.0.0
