from flask import Flask, Response
import cv2
import time
import threading
import numpy as np

from picamera2 import Picamera2

from detector import detect_pothole
from navigation import decide_action
from arduino_comm import send_command
from database import init_database, save_pothole_detection, get_detection_stats, close_database
from gps import get_gps_location

app = Flask(__name__)

FRAME_WIDTH = 320
FRAME_HEIGHT = 320

# -----------------------------
# Camera setup
# -----------------------------
picam2 = Picamera2()

config = picam2.create_preview_configuration(
    main={"size": (FRAME_WIDTH, FRAME_HEIGHT), "format": "RGB888"},
    buffer_count=4
)

picam2.configure(config)
picam2.start()
print("Camera started")

# -----------------------------
# Database
# -----------------------------
db_ready = init_database()

# -----------------------------
# Shared frame
# -----------------------------
latest_frame = None
lock = threading.Lock()

# -----------------------------
# GPS background thread
# -----------------------------
gps_lat, gps_lon = None, None

def gps_loop():
    global gps_lat, gps_lon
    while True:
        try:
            lat, lon = get_gps_location()
            if lat and lon:
                gps_lat, gps_lon = lat, lon
                print("GPS updated:", gps_lat, gps_lon)
        except Exception as e:
            print("GPS loop error:", e)
        time.sleep(5)

threading.Thread(target=gps_loop, daemon=True).start()
print("GPS thread started")


# -----------------------------
# Camera loop
# -----------------------------
def capture_loop():

    global latest_frame

    target_fps = 15
    frame_time = 1.0 / target_fps

    frame_counter = 0

    last_save_time = 0
    save_interval = 5          # ← reduced from 10

    prev_time = time.time()

    # persist last detection across frames
    detected = False
    cx, cy = 0, 0
    box = None
    detection_count = 0        # ← count consecutive detections

    while True:

        loop_start = time.time()

        try:
            # -------------------------
            # Capture
            # -------------------------
            frame = picam2.capture_array()

            current_time = time.time()
            loop_time = current_time - prev_time
            fps = min(1 / loop_time if loop_time > 0 else 0, target_fps)
            prev_time = current_time

            frame_counter += 1

            # -------------------------
            # Run inference every 5th frame
            # persists detection across non-inference frames
            # -------------------------
            if frame_counter % 8 == 0:
                new_detected, new_cx, new_cy, new_box = detect_pothole(frame)
                if new_detected:
                    detected, cx, cy, box = new_detected, new_cx, new_cy, new_box
                    detection_count += 1
                else:
                    detection_count = 0
                    detected, cx, cy, box = False, 0, 0, None

            # -------------------------
            # Navigation
            # -------------------------
            command = decide_action(detected, cx if detected else 0, cy if detected else 0)
            send_command(command)

            # -------------------------
            # Draw box + label
            # -------------------------
            if detected and box is not None:
                x1, y1, x2, y2 = box
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
                cv2.putText(frame, "POTHOLE", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

            # -------------------------
            # State log
            # -------------------------
            print("Pothole detected" if detected else "Clear", "| FPS:", int(fps))

            # -------------------------
            # DB save — wait for 2 consecutive detections
            # -------------------------
            if detected and db_ready and detection_count >= 1:
                if current_time - last_save_time > save_interval:
                    if gps_lat is not None and gps_lon is not None:
                        success, doc_id = save_pothole_detection(frame, gps_lat, gps_lon, confidence=None)
                        if success:
                            print(f"Saved to Atlas [{doc_id}] | GPS: {gps_lat:.6f}, {gps_lon:.6f}")
                        else:
                            print("Save failed — check DB logs")
                        last_save_time = current_time
                    else:
                        print("GPS not ready — skipping save")
                        last_save_time = current_time

            # -------------------------
            # FPS display
            # -------------------------
            cv2.putText(frame, f"FPS: {int(fps)}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            cv2.putText(frame, f"CMD: {command}", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

            cv2.putText(frame,
                        "POTHOLE" if detected else "CLEAR",
                        (10, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                        (0, 0, 255) if detected else (0, 255, 0), 2)

            # -------------------------
            # Share frame
            # -------------------------
            with lock:
                latest_frame = frame.copy()

            # -------------------------
            # FPS cap
            # -------------------------
            elapsed = time.time() - loop_start
            sleep_time = frame_time - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

        except Exception as e:
            print("Camera Error:", e)


threading.Thread(target=capture_loop, daemon=True).start()
print("Capture thread started")


# -----------------------------
# Stream generator
# -----------------------------
def generate():
    global latest_frame

    while True:
        try:
            with lock:
                frame = None if latest_frame is None else latest_frame.copy()

            if frame is None:
                time.sleep(0.1)
                continue

            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            if not ret:
                continue

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' +
                   buffer.tobytes() + b'\r\n')

            time.sleep(0.033)

        except Exception as e:
            print("Stream error:", e)
            time.sleep(0.1)


# -----------------------------
# Routes
# -----------------------------
@app.route('/')
def home():
    return """
    <h2>Pothole Detection System</h2>
    <img src="/video" width="640">
    """

@app.route('/video')
def video():
    return Response(generate(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/stats')
def stats():
    return get_detection_stats()


# -----------------------------
# Run
# -----------------------------
if __name__ == '__main__':
    try:
        app.run(
            host='0.0.0.0',
            port=5000,
            threaded=True,
            debug=False,
            use_reloader=False
        )
    finally:
        close_database()
        picam2.stop()
