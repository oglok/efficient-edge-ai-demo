podman build -f containerfiles/webserver.Containerfile -t quay.io/oglok/efficient-edge-ai-demo-webserver:jetpack-6 src/

podman build -f containerfiles/vicunaserver.Containerfile --runtime /usr/bin/nvidia-container-runtime -t quay.io/oglok/efficient-edge-ai-demo-vicunaserver:jetpack-6 src/

podman build -f containerfiles/yoloserver.Containerfile --runtime /usr/bin/nvidia-container-runtime -t quay.io/oglok/efficient-edge-ai-demo-yoloserver:jetpack-6 src/
