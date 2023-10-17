# This file will contain functions to run YOLOv8 on incoming streams and frames
# and return the bounding boxes of detected objects

import cv2
from ultralytics import YOLO
import torch
import numpy as np
import array

# Initialize YOLOv8 model using a cuda device
model = YOLO('yolov8n.pt')

# TODO
# The above model/library load we'll want to offload to a startup/warmup

item_list = array.array('i', [0,0,0])

# TODO should we include error checking in here for invalid frames/stream end?

# The following detect_objects function will take in a frame and return a frame with bounding boxes
# processed by YOLOv8
def detect_objects(frame, logger, cam_ip):
    
    # grab results object from a track request to the yolov8 model
    # using provided frame, confidence minimum of 50%, and hiding verbosity
    # the log spam is really inefficient on the edge devices
    results = model.track(frame, conf=0.5, verbose=False)

    # bounding boxes are at results[0].boxes, but the IDs are taking me some time to figure out
    # TODO: implement ID detection as item_list[category] = max(i, j) the returned ID from the boxes
    # will match the array index

    # plot the results into a numpy image
    frame = results[0].plot(showconf=False)

    # return the results
    return frame

def get_chairs():
    return item_list[0]

def get_people():
    return item_list[1]

def get_laptops():
    return item_list[2]
