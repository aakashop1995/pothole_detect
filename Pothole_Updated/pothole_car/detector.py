import cv2
import numpy as np
import onnxruntime as ort

# --------------------------------
# Constants
# --------------------------------
MODEL_SIZE = 320

CONF_THRESHOLD = 0.25
NMS_THRESHOLD = 0.4

# --------------------------------
# LETTERBOX (prevents zoom + distortion)
# --------------------------------
def letterbox(img, size=320):

    # --------------------------------
    # HANDLE DIFFERENT CAMERA FORMATS
    # --------------------------------

    # Grayscale
    if len(img.shape) == 2:

        img = cv2.cvtColor(
            img,
            cv2.COLOR_GRAY2BGR
        )

    # 4 channel image
    elif len(img.shape) == 3 and img.shape[2] == 4:

        # Remove alpha channel
        img = img[:, :, :3]

    h, w = img.shape[:2]

    # --------------------------------
    # SCALE
    # --------------------------------
    scale = min(size / w, size / h)

    nw = int(w * scale)
    nh = int(h * scale)

    # --------------------------------
    # RESIZE
    # --------------------------------
    resized = cv2.resize(img, (nw, nh))

    # --------------------------------
    # CREATE CANVAS
    # --------------------------------
    canvas = np.full(
        (size, size, 3),
        114,
        dtype=np.uint8
    )

    # --------------------------------
    # PADDING
    # --------------------------------
    pad_x = (size - nw) // 2
    pad_y = (size - nh) // 2

    # --------------------------------
    # PLACE IMAGE
    # --------------------------------
    canvas[
        pad_y:pad_y + nh,
        pad_x:pad_x + nw
    ] = resized

    return canvas, scale, pad_x, pad_y
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
    "/home/jayesh/pothole_detect/Pothole_Updated/model/best.onnx",
    sess_options=options,
    providers=['CPUExecutionProvider']
)

input_name = session.get_inputs()[0].name

# --------------------------------
# Detect potholes
# --------------------------------
def detect_pothole(frame):

    original_h, original_w = frame.shape[:2]

    # --------------------------------
    # Preprocess with letterbox
    # --------------------------------
    img, scale, pad_x, pad_y = letterbox(
        frame,
        MODEL_SIZE
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

    boxes = []
    confidences = []

    # --------------------------------
    # YOLO PARSING
    # --------------------------------
    for detection in predictions:

        x_center = detection[0]
        y_center = detection[1]

        width = detection[2]
        height = detection[3]

        confidence = float(detection[4])

        if confidence < CONF_THRESHOLD:
            continue

        # YOLO center -> corner
        x1 = x_center - width / 2
        y1 = y_center - height / 2

        x2 = x_center + width / 2
        y2 = y_center + height / 2

        # Remove letterbox
        x1 = (x1 - pad_x) / scale
        y1 = (y1 - pad_y) / scale

        x2 = (x2 - pad_x) / scale
        y2 = (y2 - pad_y) / scale

        # Clip
        x1 = max(0, min(original_w, x1))
        y1 = max(0, min(original_h, y1))

        x2 = max(0, min(original_w, x2))
        y2 = max(0, min(original_h, y2))

        w = int(x2 - x1)
        h = int(y2 - y1)

        # Ignore tiny boxes
        if w < 20 or h < 20:
            continue

        boxes.append([
            int(x1),
            int(y1),
            w,
            h
        ])

        confidences.append(confidence)

    # --------------------------------
    # NMS
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

            potholes.append(
                (
                    x,
                    y,
                    w,
                    h,
                    center_x,
                    center_y,
                    confidences[i]
                )
            )

    return potholes
