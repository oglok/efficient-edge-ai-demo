podman build -f webserver.Dockerfile -t quay.io/alexander_mevec/efficient-edge-demo:webserver .

podman build -f vicunaserver.Dockerfile --runtime /usr/bin/nvidia-container-runtime -t quay.io/alexander_mevec/efficient-edge-demo:vicunaserver .

podman build -f yoloserver.Dockerfile --runtime /usr/bin/nvidia-container-runtime -t quay.io/alexander_mevec/efficient-edge-demo:yoloserver .
