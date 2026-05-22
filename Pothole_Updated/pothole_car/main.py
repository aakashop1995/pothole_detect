from flask import Flask, Response
import cv2
import time
import threading
from gps import get_gps_location
from picamera2 import Picamera2

from detector import detect_pothole
from navigation import decide_action
from arduino_comm import send_command
from database import init_database, save_pothole_detection, get_detection_stats, close_database

app = Flask(__name__)

FRAME_WIDTH = 320
FRAME_HEIGHT = 240

# --------------------------------
# Camera setup
# --------------------------------
picam2 = Picamera2()

config = picam2.create_preview_configuration(
    main={"size": (FRAME_WIDTH, FRAME_HEIGHT)}
)

picam2.configure(config)
picam2.start()

print("Camera started")

# --------------------------------
# Database setup
# --------------------------------
db_ready = init_database()

if not db_ready:
    print("⚠ Warning: Database not available")

# --------------------------------
# Shared frame
# --------------------------------
latest_frame = None
lock = threading.Lock()

# --------------------------------
# Camera thread
# --------------------------------
def capture_loop():

    global latest_frame

    # FPS CAP SETTINGS
    target_fps = 30
    frame_time = 1.0 / target_fps

    frame_counter = 0

    last_gps_time = 0
    gps_interval = 5

    last_save_time = 0
    save_interval = 10

    prev_time = time.time()

    potholes = []
    last_state = None
    lat, lon = None, None

    while True:

        loop_start = time.time()

        try:

            # --------------------------------
            # Capture frame
            # --------------------------------
            frame = picam2.capture_array()

            # frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            # frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

            # --------------------------------
            # Detection every 3 frames
            # --------------------------------
            frame_counter += 1

            if frame_counter % 6 == 0:
                potholes = detect_pothole(frame)

            detected = len(potholes) > 0

            # --------------------------------
            # Navigation
            # --------------------------------
            if detected:

                nearest = max(potholes, key=lambda p: p[5])
                x, y, w, h, cx, cy = nearest

                command = decide_action(True, cx, cy)

            else:

                command = decide_action(False, 0, 0)

            send_command(command)

            # --------------------------------
            # Draw detections
            # --------------------------------
            for p in potholes:

                x, y, w, h, cx, cy = p

                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                cv2.circle(frame, (cx, cy), 5, (255, 0, 0), -1)

            # --------------------------------
            # State change print
            # --------------------------------
            if detected != last_state:

                if detected:
                    print("Pothole detected")
                else:
                    print("No pothole")

                last_state = detected

            current_time = time.time()

            # --------------------------------
            # GPS + DB (only when detected)
            # --------------------------------
            if detected:

                if current_time - last_gps_time > gps_interval:

                    lat, lon = get_gps_location()
                    print("GPS:", lat, lon)
                    last_gps_time = current_time

                if (
                    db_ready
                    and current_time - last_save_time > save_interval
                ):

                    success, doc_id = save_pothole_detection(
                        frame,
                        lat,
                        lon,
                        confidence=None
                    )

                    if success:
                        print("Saved to MongoDB")

                    last_save_time = current_time

            # --------------------------------
            # FPS calculation
            # --------------------------------
            fps = 1 / (current_time - prev_time)
            prev_time = current_time

            cv2.putText(frame, f"FPS: {int(fps)}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            cv2.putText(frame, f"CMD: {command}", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

            cv2.putText(frame,
                        "POTHOLE" if detected else "CLEAR",
                        (10, 90),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 0, 255) if detected else (0, 255, 0),
                        2)

            # --------------------------------
            # Update shared frame
            # --------------------------------
            with lock:
                latest_frame = frame.copy()

            # --------------------------------
            # FPS CAP (30 FPS)
            # --------------------------------
            elapsed = time.time() - loop_start

            if elapsed < frame_time:
                time.sleep(frame_time - elapsed)

        except Exception as e:
            print("Camera Error:", e)

# Start thread
threading.Thread(target=capture_loop, daemon=True).start()

# --------------------------------
# MJPEG Stream
# --------------------------------
def generate():

    global latest_frame

    while True:

        with lock:
            frame = None if latest_frame is None else latest_frame.copy()

        if frame is None:
            continue

        success, buffer = cv2.imencode('.jpg', frame,
                                        [int(cv2.IMWRITE_JPEG_QUALITY), 80])

        if not success:
            continue

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' +
               buffer.tobytes() + b'\r\n')

        time.sleep(0.08)

# --------------------------------
# Flask routes
# --------------------------------
@app.route('/')

def home():

    return """
    <html>
        <body>
            <h2>Pothole Detection Car</h2>
            <img src="/video" width="640"/>
        </body>
    </html>
    """

@app.route('/video')

def video():

    return Response(generate(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/stats')

def stats():

    stats_data = get_detection_stats()

    return {
        "total_detections": stats_data.get("total_detections", 0),
        "last_updated": str(stats_data.get("last_updated", "N/A"))
    }

# --------------------------------
# Run server
# --------------------------------
if __name__ == '__main__':

    try:
        app.run(
            host='0.0.0.0',
            port=5000,
            threaded=True,
            debug=False,
            use_reloader=False
        )

    except KeyboardInterrupt:
        print("\nShutting down...")
        close_database()
        picam2.stop()

    finally:
        close_database()
        picam2.stop()
