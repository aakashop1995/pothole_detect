import cv2
import numpy as np
import onnxruntime as ort

MODEL_SIZE = 320
CONF_THRESHOLD = 0.3
FRAME_WIDTH = 320
FRAME_HEIGHT = 320

# -------------------------------
# Load ONNX model ONCE
# -------------------------------
options = ort.SessionOptions()
options.intra_op_num_threads = 1
options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

session = ort.InferenceSession(
    "/home/jayesh/Pothole_detection/model/best.onnx",
    sess_options=options,
    providers=["CPUExecutionProvider"]
)

input_name = session.get_inputs()[0].name


# -------------------------------
# Detect pothole (SINGLE OUTPUT)
# -------------------------------
def detect_pothole(frame):

    try:
        img = cv2.resize(frame, (MODEL_SIZE, MODEL_SIZE))
        img = img.astype(np.float32) / 255.0
        img = np.transpose(img, (2, 0, 1))
        img = np.expand_dims(img, axis=0)

        outputs = session.run(None, {input_name: img})
        predictions = np.squeeze(outputs[0])

        if len(predictions.shape) == 1:
            return False, 0, 0

        for det in predictions:

            if len(det) < 5:
                continue

            x_c, y_c, w, h, conf = det[:5]

            if conf < CONF_THRESHOLD:
                continue

            x1 = int((x_c - w / 2) * FRAME_WIDTH / MODEL_SIZE)
            y1 = int((y_c - h / 2) * FRAME_HEIGHT / MODEL_SIZE)
            x2 = int((x_c + w / 2) * FRAME_WIDTH / MODEL_SIZE)
            y2 = int((y_c + h / 2) * FRAME_HEIGHT / MODEL_SIZE)

            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2

            # Only lower half (road logic)
            if cy > FRAME_HEIGHT // 2:
                return True, cx, cy

        return False, 0, 0

    except Exception as e:
        print("Detector error:", e)
        return False, 0, 0
