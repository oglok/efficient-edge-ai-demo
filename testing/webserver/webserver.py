from flask import request, Response, Flask, render_template
import logging
import time
import sys
import grpc
import yoloserving_pb2
import yoloserving_pb2_grpc


from mlc_chat import ChatModule
from mlc_chat.callback import StreamIterator
from threading import Thread

# frame to be shared via mjpeg server out
app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.disabled = True
app.logger.disabled = True
fps = 0
infstr = ""

@app.route("/get_inf")
def getinf():
    global infstr
    return infstr

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route('/res',methods = ['POST','GET'])
def res():
    result = request.form.to_dict()
    return render_template("results.html")

@app.route('/results')
def video_feed():
	return Response(generate_video_feed(),mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/test_func', methods=['GET'])
def test_func():
    global fps
    return (str(round(fps,2)))

@app.route('/inf')
def inf():
    global infstr
    infstr = ""
    # print the completion
    cm = ChatModule(model="params")

    print("Inferencing...")

    stream = StreamIterator(callback_interval=2)
    generation_thread = Thread(
       target=cm.generate,
       kwargs={"prompt": "Can you tell me what a room with 75 people, 100 chairs, and 2 laptops might be used for??", "progress_callback": stream},
    )
    generation_thread.start()

    for delta_message in stream:
       infstr += delta_message
       
    generation_thread.join()
    

def generate_video_feed():
    global fps
    while True:
       start_time = time.time()
       with grpc.insecure_channel("yoloserver.efficient-edge-ai.svc.cluster.local:50051") as channel:
           stub = yoloserving_pb2_grpc.MultiYoloStub(channel)
           for response in stub.yoloInference(
              yoloserving_pb2.YoloRequest(model="yolov8n.engine",vid="0")):
                yield b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + response.image + b'\r\n'
                fps = 1.0 / (time.time() - start_time)
                start_time = time.time()
