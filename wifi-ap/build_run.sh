#!/bin/sh
podman build -f Dockerfile.rpi4 -t quay.io/oglok/microshift-ap-cams:latest
podman run -ti --rm --privileged --net=host --name wifiap quay.io/oglok/microshift-ap-cams:latest

