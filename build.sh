podman build -f docker/webserver.Dockerfile -t quay.io/alexander_mevec/efficient-edge-demo:webserver src/

podman build -f docker/vicunaserver.Dockerfile --runtime /usr/bin/nvidia-container-runtime -t quay.io/alexander_mevec/efficient-edge-demo:vicunaserver src/

podman build -f docker/yoloserver.Dockerfile --runtime /usr/bin/nvidia-container-runtime -t quay.io/alexander_mevec/efficient-edge-demo:yoloserver src/
