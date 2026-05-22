import cv2
import numpy as np
import onnxruntime as ort

# --------------------------------
# Constants
# --------------------------------
MODEL_SIZE = 320

CONF_THRESHOLD = 0.25

FRAME_WIDTH = 320
FRAME_HEIGHT = 320

# --------------------------------
# Load ONNX model
# --------------------------------
options = ort.SessionOptions()

options.intra_op_num_threads = 1

options.graph_optimization_level = (
    ort.GraphOptimizationLevel.ORT_ENABLE_ALL
)

session = ort.InferenceSession(
    "/home/jayesh/Pothole_detection/model/best.onnx",
    sess_options=options,
    providers=['CPUExecutionProvider']
)

input_name = session.get_inputs()[0].name

# --------------------------------
# Detect pothole
# --------------------------------
def detect_pothole(frame):

    # --------------------------------
    # Resize
    # --------------------------------
    img = cv2.resize(
        frame,
        (MODEL_SIZE, MODEL_SIZE)
    )

    # --------------------------------
    # Normalize
    # --------------------------------
    img = img.astype(np.float32) / 255.0

    # HWC -> CHW
    img = np.transpose(img, (2, 0, 1))

    # Batch dimension
    img = np.expand_dims(img, axis=0)

    # --------------------------------
    # Inference
    # --------------------------------
    outputs = session.run(
        None,
        {input_name: img}
    )

    predictions = outputs[0]

    # --------------------------------
    # FIX SHAPE
    # (1, 5, 2100) -> (2100, 5)
    # --------------------------------
    if len(predictions.shape) == 3:

        predictions = np.transpose(
            predictions,
            (0, 2, 1)
        )

        predictions = predictions[0]

    # --------------------------------
    # Parse detections
    # --------------------------------
    for detection in predictions[::2]:

        confidence = float(detection[4])

        if confidence < CONF_THRESHOLD:
            continue

        x_center = detection[0]
        y_center = detection[1]

        width = detection[2]
        height = detection[3]

        # Convert coordinates
        x1 = int(
            (x_center - width / 2)
            * FRAME_WIDTH
            / MODEL_SIZE
        )

        y1 = int(
            (y_center - height / 2)
            * FRAME_HEIGHT
            / MODEL_SIZE
        )

        x2 = int(
            (x_center + width / 2)
            * FRAME_WIDTH
            / MODEL_SIZE
        )

        y2 = int(
            (y_center + height / 2)
            * FRAME_HEIGHT
            / MODEL_SIZE
        )

        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2

        # Only near potholes
        if center_y > FRAME_HEIGHT // 2:

            return True, center_x, center_y

    return False, 0, 0
