import requests
from flask import Flask, send_file, Response
import socket
import logging
import os
import cv2


def register(ip, token):
    return requests.get("http://microshift-cam-reg.local/register?ip=" + ip + "&token=" + token)

app = Flask(__name__)
app.logger.setLevel(logging.INFO)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # doesn't even have to be reachable
        s.connect(('10.254.254.254', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP
IPAddr = get_ip()

# Register the camera with the server running in the host microshift-cam-reg.local
register(str(IPAddr), "12345678901234567890123456789012")

video_path = 'video.mp4'  # Replace with the path to your video file
cap = cv2.VideoCapture(video_path)

@app.route('/stream')
def stream_video():
    if not cap.isOpened():
        return "Video capture failed", 500

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Process the frame here (if needed)
        # You can convert the frame to JPEG or perform other operations

        _, encoded_frame = cv2.imencode('.jpg', frame)
        if not _:
            return "Error encoding frame to JPEG", 500

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + encoded_frame.tobytes() + b'\r\n')

# Start the webserver
app.run(host=str(IPAddr), port=8020)

