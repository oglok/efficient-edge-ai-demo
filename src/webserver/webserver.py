from flask import request, Response, Flask, render_template
import logging
import time
import sys
import grpc
import yoloserving_pb2
import yoloserving_pb2_grpc
import vicunaserving_pb2
import vicunaserving_pb2_grpc
import redis
from threading import Thread

# Start flask app
app = Flask(__name__)

context = ""

# Connect to redis server
red = redis.StrictRedis('localhost', 6379, 0, charset='utf-8', decode_responses=True)

# Health check
@app.route("/healthy")
def healthy():
    return "Healthy"

# Return the llm event stream
@app.route("/llm_stream")
def llm_stream():
    return Response(readllm(), mimetype="text/event-stream")

# Return the video stream frames for embedding
@app.route("/vid_stream")
def vid_stream():
        return Response(generate_video_feed(),mimetype='multipart/x-mixed-replace; boundary=frame')

# Load the demo web page
@app.route('/',methods = ['POST','GET'])
def res():
    result = request.form.to_dict()
    return render_template("demo.html")

# Return the FPS of the YOLO inference service
@app.route('/fps_stream', methods=['GET'])
def fps():
    return Response(readfps(), mimetype="text/event-stream")

# Begin the inference call to vicunaservice
@app.route('/llm', methods = ['POST'])
def inf():
    global context
    prompt = context + request.form.get("prompt_data")
    print(prompt)
    Thread(target=generate_text_feed, args=(prompt,request.form.get("prompt_context"))).start()
    return prompt

# Async listener for pubsub feed of LLM data
def readllm():
    pubsub = red.pubsub()
    pubsub.subscribe('llm')
    for message in pubsub.listen():
        yield 'data: %s\n\n' % message['data']

# Caller to LLM service to begin text generation
def generate_text_feed(prompt_data, prompt_context):
    # Open a gRPC connection to our vicuna service
    with grpc.insecure_channel("vicunaserver.efficient-edge-demo.svc.cluster.local:50051") as channel:
        # Get the gRPC stub to our channel
        stub = vicunaserving_pb2_grpc.MultiVicunaStub(channel)
        # Add default "Assistant: " response to delineate between user/generated output
        red.publish('llm', "Assistant: ")
        # Use the gRPC stub to get our stream
        for response in stub.vicunaInference(
                vicunaserving_pb2.VicunaRequest(prompt=prompt_data, context=prompt_context)):
            # Publish results to redis llm topic
            red.publish('llm', response.reply)
        # Publish some cleanup items to the llm topic
        red.publish('llm', "<newline>User: ")
        red.publish('llm', "<focus>")

# Async listener to pubsub feed of FPS data
def readfps():
    pubsub = red.pubsub()
    pubsub.subscribe('fps')
    for message in pubsub.listen():
        yield 'data: %s\n\n' % message['data']

# Caller to computer vision service to begin video feed inferencing
def generate_video_feed():
    global context
    # Loop this feed forever (this makes restarting the pod/webcam required to reload the webpage, not optimal)
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
                    # context labels formatted by yoloserver
                    context = response.labels
                    # Publish FPS stat
                    red.publish('fps', str(round(1.0 / (time.time() - start_time),2)))
                    # Yield the encoded bytebuffer of the frame to our renderer
                    yield b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + response.image + b'\r\n'
                    start_time = time.time()
