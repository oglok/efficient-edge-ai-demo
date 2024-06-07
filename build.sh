podman build -f docker/webserver.Dockerfile -t quay.io/oglok/efficient-edge-ai-demo-webserver:jetpack-6 src/

podman build -f docker/vicunaserver.Dockerfile --runtime /usr/bin/nvidia-container-runtime -t quay.io/oglok/efficient-edge-ai-demo-vicunaserver:jetpack-6 src/

podman build -f docker/yoloserver.Dockerfile --runtime /usr/bin/nvidia-container-runtime -t quay.io/oglok/efficient-edge-ai-demo-yoloserver:jetpack-6 src/
