import asyncio
import logging
import cv2
from ultralytics import YOLO
import grpc
from yoloserving_pb2 import YoloReply
from yoloserving_pb2 import YoloRequest
from yoloserving_pb2_grpc import MultiYoloServicer
from yoloserving_pb2_grpc import add_MultiYoloServicer_to_server
import supervision as sv
from collections import Counter

class YoloServing(MultiYoloServicer):
    async def yoloInference(self, request: YoloRequest,
                       context: grpc.aio.ServicerContext) -> YoloReply:
        logging.info("Serving the requested inferencing")

        # Prepare box annotator
        box_annotator = sv.BoxAnnotator(
        thickness=2,
        text_thickness=1,
        text_scale=0.5
        )

        # Prepare labels for TensorRT model, as the compiled model does not contain these IDs
        names = {
            0: 'person', 1: 'bicycle', 2: 'car', 3: 'motorcycle', 4: 'airplane', 5: 'bus',
            6: 'train', 7: 'truck', 8: 'boat', 9: 'traffic light', 10: 'fire hydrant',
            11: 'stop sign', 12: 'parking meter', 13: 'bench', 14: 'bird', 15: 'cat',
            16: 'dog', 17: 'horse', 18: 'sheep', 19: 'cow', 20: 'elephant', 21: 'bear',
            22: 'zebra', 23: 'giraffe', 24: 'backpack', 25: 'umbrella', 26: 'handbag',
            27: 'tie', 28: 'suitcase', 29: 'frisbee', 30: 'skis', 31: 'snowboard',
            32: 'sports ball', 33: 'kite', 34: 'baseball bat', 35: 'baseball glove',
            36: 'skateboard', 37: 'surfboard', 38: 'tennis racket', 39: 'bottle',
            40: 'wine glass', 41: 'cup', 42: 'fork', 43: 'knife', 44: 'spoon',
            45: 'bowl', 46: 'banana', 47: 'apple', 48: 'sandwich', 49: 'orange',
            50: 'broccoli', 51: 'carrot', 52: 'hot dog', 53: 'pizza', 54: 'donut',
            55: 'cake', 56: 'chair', 57: 'couch', 58: 'potted plant', 59: 'bed',
            60: 'dining table', 61: 'toilet', 62: 'tv', 63: 'laptop', 64: 'mouse',
            65: 'remote', 66: 'keyboard', 67: 'cell phone', 68: 'microwave',
            69: 'oven', 70: 'toaster', 71: 'sink', 72: 'refrigerator', 73: 'book',
            74: 'clock', 75: 'vase', 76: 'scissors', 77: 'teddy bear',
            78: 'hair drier', 79: 'toothbrush'
        }
        # Instantiate the YOLOv8n TensorRT model
        model = YOLO("yolov8n.engine")

        # Load watermark image
        watermark = cv2.imread("watermark.png")

        # Create an iterator for all produced frames on the input stream "device=0" (/dev/video0)
        for result in model(source=0, device=0, show=True, stream=True, agnostic_nms=True, verbose=False):

            # Store our frame for bounding boxes later
            frame = result.orig_img

            # Calculate the dimensions for the watermark (e.g., 10% of the frame width)
            frame_height, frame_width, _ = frame.shape
            watermark_height = int(frame_height * 0.2)  # Adjust the size as needed
            watermark_width = int(watermark_height * watermark.shape[1] / watermark.shape[0])

            # Calculate the position for the watermark (right bottom corner)
            x_offset = frame_width - watermark_width
            y_offset = frame_height - watermark_height

            # Resize the watermark to the calculated dimensions
            watermark = cv2.resize(watermark, (watermark_width, watermark_height))
            frame[y_offset:y_offset+watermark_height, x_offset:x_offset+watermark_width] = watermark

            # Extract detections from the model result
            detections = sv.Detections.from_ultralytics(result)

            # Prepare all labels
            labels = [
                f"{names[class_id]}"
                for _,_,_,class_id,_,_
                in detections
            ]

            labelCounter = Counter(labels)

            countedLabels = ""

            for key, num in labelCounter.items():
              countedLabels += "There are " + str(num) + " " + key + " in this room right now. "

            # Annotate our frame with our detections and labels
            frame = box_annotator.annotate(
                scene=frame,
                detections=detections,
                labels=labels
            )

            # Encode our image into jpg for the web page later
            encodedImage = cv2.imencode(".jpg", frame)[1]

            # Encode our image to bytes for our GRPC response
            imgstring = encodedImage.tobytes()

            # Yield back our YoloReply
            yield YoloReply(labels=countedLabels,image=imgstring)

def precache_model():
    # Pre-run inference to "warm up" the engine file into memory using the
    model = YOLO("yolov8n.engine")
    model.track(source="image.jpg", device=0, show=False, stream=False, agnostic_nms=True, verbose=False)

# async serve function for the grpc server
async def serve() -> None:

    # Model warmup
    precache_model()

    # Instantiate a server on 50051
    server = grpc.aio.server()
    add_MultiYoloServicer_to_server(YoloServing(), server)
    listen_addr = "[::]:50051"
    server.add_insecure_port(listen_addr)
    logging.info("Starting server on %s", listen_addr)
    await server.start()
    await server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(serve())

