from flask import Flask, Response
import cv2
import time
import threading

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
# Camera loop
# -----------------------------
def capture_loop():

    global latest_frame

    target_fps = 30
    frame_time = 1.0 / target_fps

    frame_counter = 0

    last_gps_time = 0
    gps_interval = 5

    last_save_time = 0
    save_interval = 10

    prev_time = time.time()

    detected = False
    cx, cy = 0, 0

    lat, lon = None, None

    while True:

        loop_start = time.time()

        try:

            frame = picam2.capture_array()

            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            frame_counter += 1

            # -------------------------
            # Run detection every 3 frames
            # -------------------------
            if frame_counter % 3 == 0:
                detected, cx, cy = detect_pothole(frame)

            # -------------------------
            # Navigation
            # -------------------------
            if detected:
                command = decide_action(True, cx, cy)
            else:
                command = decide_action(False, 0, 0)

            send_command(command)

            # -------------------------
            # Draw
            # -------------------------
            if detected:
                cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)

            # -------------------------
            # State log
            # -------------------------
            if detected:
                print("Pothole detected")
            else:
                print("Clear")

            # -------------------------
            # GPS + DB
            # -------------------------
            current_time = time.time()

            if detected:

                if current_time - last_gps_time > gps_interval:
                    lat, lon = get_gps_location()
                    print("GPS:", lat, lon)
                    last_gps_time = current_time

                if db_ready and current_time - last_save_time > save_interval:
                    save_pothole_detection(frame, lat, lon, None)
                    print("Saved to DB")
                    last_save_time = current_time

            # -------------------------
            # FPS
            # -------------------------
            fps = 1 / (current_time - prev_time)
            prev_time = current_time

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
            if elapsed < frame_time:
                time.sleep(frame_time - elapsed)

        except Exception as e:
            print("Camera Error:", e)


# Start thread
threading.Thread(target=capture_loop, daemon=True).start()


# -----------------------------
# Stream generator
# -----------------------------
def generate():

    global latest_frame

    while True:

        with lock:
            frame = None if latest_frame is None else latest_frame.copy()

        if frame is None:
            continue

        _, buffer = cv2.imencode('.jpg', frame)

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' +
               buffer.tobytes() + b'\r\n')

        time.sleep(0.05)


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
            threaded=False,
            debug=False,
            use_reloader=False
        )

    finally:
        close_database()
        picam2.stop()
