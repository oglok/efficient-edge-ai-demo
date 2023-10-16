# This file will contain functions to run YOLOv8 on incoming streams and frames
# and return the bounding boxes of detected objects

import cv2
from ultralytics import YOLO
import torch
import numpy as np

# Initialize YOLOv8 model using a cuda device
model = YOLO('yolov8n.pt')
#model.to('cuda')

# The following detect_objects function will take in a frame and return a frame with bounding boxes
# processed by YOLOv8
def detect_objects(frame, logger, cam_ip):
    results = model.track(frame, persist=True)
    return frame
