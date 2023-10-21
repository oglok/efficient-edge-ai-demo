from flask import request
from flask import Response
from flask import Flask
import logging
import cv2
from ultralytics import YOLO
import supervision as sv
import time

# frame to be shared via mjpeg server out
app = Flask(__name__)
app.logger.setLevel(logging.INFO)

yolo = YOLO("yolov8n.pt")
byte_tracker = sv.ByteTrack()
annotator = sv.BoxAnnotator()

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route("/video_feed")
def video_feed():
    # return the response generated along with the specific media
    # type (mime type)
    return Response(generate_video_feed(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/video_feed1")
def video_feed1():
    # return the response generated along with the specific media
    # type (mime type)
    return Response(generate_video_feed1(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")

def generate_video_feed():

    cam = cv2.VideoCapture(0)
    totalframes = 0
    averagefps = 0

    # loop over frames from the output stream
    while cam.isOpened():

        ret, img = cam.read()
        start_time = time.time()
        if ret:
            # encode the frame in JPEG format
            #(flag, encodedImage) = cv2.imencode(".jpg", img)
            img = cv2.resize(img,(853,480))
            results = yolo(img, verbose=False)[0]
            detections = sv.Detections.from_ultralytics(results)
            detections = byte_tracker.update_with_detections(detections)
            labels = [
                f"#{tracker_id} {yolo.model.names[class_id]} {confidence:0.5f}"
               for _, _, confidence, class_id, tracker_id
              in detections
            ]
            (flag, encodedImage) = cv2.imencode(".jpg", annotator.annotate(scene=img.copy(), detections=detections, labels=labels))

        else:
            break
        totalframes += 1
        averagefps += 1.0 / (time.time() - start_time)

        print("FPS:", 1.0 / (time.time() - start_time))

        # ensure the frame was successfully encoded
        if not flag:
            continue

        # yield the output frame in the byte format
        yield b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n'

    cam.release()
	
	
def generate_video_feed1():

    cam = cv2.VideoCapture(0)
    totalframes = 0
    averagefps = 0

    # loop over frames from the output stream
    while cam.isOpened():

        ret, img = cam.read()
        start_time = time.time()
        if ret:
            # encode the frame in JPEG format
            img = cv2.resize(img,(853,480))
            results = yolo.track(img, verbose=False)
            (flag, encodedImage) = cv2.imencode(".jpg", results[0].plot())

        else:
            break
        totalframes += 1
        averagefps += 1.0 / (time.time() - start_time)

        print("FPS:", 1.0 / (time.time() - start_time))

        # ensure the frame was successfully encoded
        if not flag:
            continue

        # yield the output frame in the byte format
        yield b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n'

    cam.release()
