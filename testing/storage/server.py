from flask import request, Response, Flask, render_template
import logging
import cv2
from ultralytics import YOLO
import supervision as sv
import time
from mlc_chat import ChatModule
from mlc_chat.callback import StreamIterator
from threading import Thread
import sys

# frame to be shared via mjpeg server out
app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.disabled = True
app.logger.disabled = True
fps = 0
infstr = ""

model = YOLO("yolov8n.engine")
model.track(source="image.jpg", device=0, show=True, stream=False, agnostic_nms=True, verbose=False)

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
    box_annotator = sv.BoxAnnotator(
        thickness=2,
        text_thickness=1,
        text_scale=0.5
    )
    names = {0: 'person', 1: 'bicycle', 2: 'car', 3: 'motorcycle', 4: 'airplane', 5: 'bus', 6: 'train', 7: 'truck', 8: 'boat', 9: 'traffic light', 10: 'fire hydrant', 11: 'stop sign', 12: 'parking meter', 13: 'bench', 14: 'bird', 15: 'cat', 16: 'dog', 17: 'horse', 18: 'sheep', 19: 'cow', 20: 'elephant', 21: 'bear', 22: 'zebra', 23: 'giraffe', 24: 'backpack', 25: 'umbrella', 26: 'handbag', 27: 'tie', 28: 'suitcase', 29: 'frisbee', 30: 'skis', 31: 'snowboard', 32: 'sports ball', 33: 'kite', 34: 'baseball bat', 35: 'baseball glove', 36: 'skateboard', 37: 'surfboard', 38: 'tennis racket', 39: 'bottle', 40: 'wine glass', 41: 'cup', 42: 'fork', 43: 'knife', 44: 'spoon', 45: 'bowl', 46: 'banana', 47: 'apple', 48: 'sandwich', 49: 'orange', 50: 'broccoli', 51: 'carrot', 52: 'hot dog', 53: 'pizza', 54: 'donut', 55: 'cake', 56: 'chair', 57: 'couch', 58: 'potted plant', 59: 'bed', 60: 'dining table', 61: 'toilet', 62: 'tv', 63: 'laptop', 64: 'mouse', 65: 'remote', 66: 'keyboard', 67: 'cell phone', 68: 'microwave', 69: 'oven', 70: 'toaster', 71: 'sink', 72: 'refrigerator', 73: 'book', 74: 'clock', 75: 'vase', 76: 'scissors', 77: 'teddy bear', 78: 'hair drier', 79: 'toothbrush'}

    model = YOLO("yolov8n.engine")
    for result in model.track(source=0, device=0, show=True, stream=True, agnostic_nms=True, verbose=False):

        start_time = time.time()
        averagefps = 0
        frame = result.orig_img
        detections = sv.Detections.from_ultralytics(result)

        if result.boxes.id is not None:
            detections.tracker_id = result.boxes.id.cpu().numpy().astype(int)

        labels = [
            f"{tracker_id} {names[class_id]} {confidence:0.2f}"
            for _, _, confidence, class_id, tracker_id
            in detections
        ]

        frame = box_annotator.annotate(
            scene=frame,
            detections=detections,
            labels=labels
        )

        (flag, encodedImage) = cv2.imencode(".jpg", frame)

        #encodedImage = cv2.resize(encodedImage,(853,480))

        fps= 1.0 / (time.time() - start_time)

        if not flag:
            continue

        yield b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n'
