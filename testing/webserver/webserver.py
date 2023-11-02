from flask import request, Response, Flask, render_template
import logging
import time
import sys
import grpc
import yoloserving_pb2
import yoloserving_pb2_grpc
import vicunaserving_pb2
import vicunaserving_pb2_grpc

# Start flask app without logging
app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.disabled = True
app.logger.disabled = True

# Instantiate global variables for passing values around
fps = 0
infstr = ""

# Health check
@app.route("/healthy")
def healthy():
    return "Healthy"

# Return the inference string to the spam function
@app.route("/get_inf")
def getinf():
    global infstr
    return infstr

# Load the demo web page and start the stream
@app.route('/',methods = ['POST','GET'])
def res():
    result = request.form.to_dict()
    return render_template("results.html")

# Return the video stream frames for embedding
@app.route('/results')
def video_feed():
        return Response(generate_video_feed(),mimetype='multipart/x-mixed-replace; boundary=frame')

# Return the FPS of the YOLO inference service
@app.route('/fps', methods=['GET'])
def fps():
    global fps
    return (str(round(fps,2)))

# Begin the inference call to vicunaservice
@app.route('/inf', methods = ['POST'])
def inf():
    # Grab our global return infstr
    global infstr
    infstr = ""
    # Open a gRPC connection to our vicuna service
    with grpc.insecure_channel("vicunaserver.efficient-edge-demo.svc.cluster.local:50051") as channel:
        # Get the gRPC stub to our channel
        stub = vicunaserving_pb2_grpc.MultiVicunaStub(channel)
        # Use the gRPC stub to get our stream
        for response in stub.vicunaInference(
                vicunaserving_pb2.VicunaRequest(prompt=request.form.get("data"), context="You are a helpful bot at a conference called KubeCon and I am the presenter asking you questions about Kubernetes.")):
            infstr += response.reply

# Create a video feed for the web page from yoloservice
def generate_video_feed():
    # Keep a global, returnable fps for our inferencing
    global fps
    # Loop this video forever
    while True:        
        # Instantiate our time
        start_time = time.time()
        # Open a gRPC connection to our yolo service
        with grpc.insecure_channel("yoloserver.efficient-edge-demo.svc.cluster.local:50051") as channel:
            # Get the gRPC stub to our channel
            stub = yoloserving_pb2_grpc.MultiYoloStub(channel)
            # Use the gRPC stub to get our stream
            for response in stub.yoloInference(
                yoloserving_pb2.YoloRequest(model="yolov8n.engine",vid="0")):
                    # Yield the encoded bytebuffer of the frame to our renderer
                    yield b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + response.image + b'\r\n'
                    # Set our FPS to display a number
                    fps = 1.0 / (time.time() - start_time)
                    start_time = time.time()
