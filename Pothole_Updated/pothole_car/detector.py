import cv2
import numpy as np
import onnxruntime as ort

# --------------------------------
# Constants
# --------------------------------
MODEL_SIZE = 320

CONF_THRESHOLD = 0.5
NMS_THRESHOLD = 0.4

# --------------------------------
# ONNX Runtime Optimization
# --------------------------------
options = ort.SessionOptions()

options.intra_op_num_threads = 2

options.graph_optimization_level = (
    ort.GraphOptimizationLevel.ORT_ENABLE_ALL
)

# --------------------------------
# Load ONNX model
# --------------------------------
session = ort.InferenceSession(
    "/home/jayesh/Pothole_detection/model/best.onnx",
    sess_options=options,
    providers=['CPUExecutionProvider']
)

input_name = session.get_inputs()[0].name

# --------------------------------
# Detect potholes
# --------------------------------
def detect_pothole(frame):

    original_h, original_w = frame.shape[:2]

    # Resize frame
    img = cv2.resize(
        frame,
        (MODEL_SIZE, MODEL_SIZE)
    )

    # BGR -> RGB
    img = cv2.cvtColor(
        img,
        cv2.COLOR_BGR2RGB
    )

    # Normalize
    img = img.astype(np.float32) / 255.0

    # HWC -> CHW
    img = np.transpose(img, (2, 0, 1))

    # Add batch dimension
    img = np.expand_dims(img, axis=0)

    # --------------------------------
    # Run inference
    # --------------------------------
    outputs = session.run(
        None,
        {input_name: img}
    )

    predictions = outputs[0][0]

    boxes = []
    confidences = []

    # --------------------------------
    # Parse detections
    # --------------------------------
    for detection in predictions:

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
            * original_w
            / MODEL_SIZE
        )

        y1 = int(
            (y_center - height / 2)
            * original_h
            / MODEL_SIZE
        )

        w = int(width * original_w / MODEL_SIZE)
        h = int(height * original_h / MODEL_SIZE)

        boxes.append([x1, y1, w, h])

        confidences.append(confidence)

    # --------------------------------
    # Apply NMS
    # --------------------------------
    indices = cv2.dnn.NMSBoxes(
        boxes,
        confidences,
        CONF_THRESHOLD,
        NMS_THRESHOLD
    )

    potholes = []

    if len(indices) > 0:

        for i in indices.flatten():

            x, y, w, h = boxes[i]

            center_x = x + w // 2
            center_y = y + h // 2

            # Only lower-half potholes
            if center_y > original_h // 2:

                potholes.append(
                    (
                        x,
                        y,
                        w,
                        h,
                        center_x,
                        center_y
                    )
                )

    return potholes