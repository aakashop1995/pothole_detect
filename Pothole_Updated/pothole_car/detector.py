import cv2
import numpy as np
import onnxruntime as ort

MODEL_SIZE = 320
CONF_THRESHOLD = 0.6
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
# Detect pothole
# -------------------------------
def detect_pothole(frame):
    try:
        img = cv2.resize(frame, (MODEL_SIZE, MODEL_SIZE))
        img = img.astype(np.float32) / 255.0
        img = np.transpose(img, (2, 0, 1))
        img = np.expand_dims(img, axis=0)

        outputs = session.run(None, {input_name: img})

        # ← KEY FIX: match laptop version
        preds = outputs[0][0].T  # (2100, 5)

        boxes = []
        scores = []

        for det in preds:
            x, y, w, h, conf = det

            if conf < CONF_THRESHOLD:
                continue

            # Auto detect normalized vs pixel
            if x <= 1.0 and y <= 1.0 and w <= 1.0 and h <= 1.0:
                x1 = int((x - w / 2) * MODEL_SIZE)
                y1 = int((y - h / 2) * MODEL_SIZE)
                x2 = int((x + w / 2) * MODEL_SIZE)
                y2 = int((y + h / 2) * MODEL_SIZE)
            else:
                x1 = int(x - w / 2)
                y1 = int(y - h / 2)
                x2 = int(x + w / 2)
                y2 = int(y + h / 2)

            # Clamp to frame
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(MODEL_SIZE, x2)
            y2 = min(MODEL_SIZE, y2)

            # Skip tiny boxes
            if x2 - x1 < 30 or y2 - y1 < 30:
                continue

            boxes.append([x1, y1, x2, y2])
            scores.append(float(conf))

        # NMS - remove duplicate boxes
        if boxes:
            indices = cv2.dnn.NMSBoxes(
                [[x1, y1, x2 - x1, y2 - y1] for x1, y1, x2, y2 in boxes],
                scores,
                CONF_THRESHOLD,
                0.4  # NMS threshold
            )

            for i in indices:
                idx = i[0] if isinstance(i, (list, np.ndarray)) else i
                x1, y1, x2, y2 = boxes[idx]
                conf = scores[idx]

                cx = (x1 + x2) // 2
                cy = (y1 + y2) // 2

                print(f"Pothole: conf={conf:.2f}, cx={cx}, cy={cy}")
                return True, cx, cy, (x1, y1, x2, y2)

        return False, 0, 0, None

    except Exception as e:
        print("Detector error:", e)
        return False, 0, 0, None
