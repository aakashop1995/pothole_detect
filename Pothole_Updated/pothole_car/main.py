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
# Picamera2 setup
# --------------------------------
picam2 = Picamera2()

config = picam2.create_preview_configuration(
    main={"size": (FRAME_WIDTH, FRAME_HEIGHT)}
)

picam2.configure(config)

picam2.start()

print("Camera started")

# --------------------------------
# MongoDB Atlas setup
# --------------------------------
db_ready = init_database()

if not db_ready:
    print("⚠ Warning: Database initialization failed. Continuing without database logging.")

# --------------------------------
# Shared frame
# --------------------------------
latest_frame = None

lock = threading.Lock()

# --------------------------------
# Camera capture thread
# --------------------------------
# --------------------------------
# Camera capture thread
# --------------------------------
def capture_loop():

    global latest_frame

    frame_counter = 0

    last_gps_time = 0
    gps_interval = 5

    last_save_time = 0
    save_interval = 10

    prev_time = time.time()

    potholes = []

    while True:

        try:

            # --------------------------------
            # Capture frame
            # --------------------------------
            frame = picam2.capture_array()

            # RGB -> BGR
            frame = cv2.cvtColor(
                frame,
                cv2.COLOR_RGB2BGR
            )

            # Resize
            frame = cv2.resize(
                frame,
                (FRAME_WIDTH, FRAME_HEIGHT)
            )

            # --------------------------------
            # Run detection every 3 frames
            # --------------------------------
            frame_counter += 1

            if frame_counter % 3 == 0:

                potholes = detect_pothole(frame)

            detected = len(potholes) > 0

            # --------------------------------
            # Navigation Logic
            # --------------------------------
            if detected:

                # Nearest pothole
                nearest = max(
                    potholes,
                    key=lambda p: p[5]
                )

                x, y, w, h, cx, cy = nearest

                command = decide_action(
                    True,
                    cx,
                    cy
                )

            else:

                command = decide_action(
                    False,
                    0,
                    0
                )

            # --------------------------------
            # Send to Arduino
            # --------------------------------
            send_command(command)

            # --------------------------------
            # Draw potholes
            # --------------------------------
            for pothole in potholes:

                x, y, w, h, cx, cy = pothole

                # Bounding box
                cv2.rectangle(
                    frame,
                    (x, y),
                    (x + w, y + h),
                    (0, 0, 255),
                    2
                )

                # Center point
                cv2.circle(
                    frame,
                    (cx, cy),
                    5,
                    (255, 0, 0),
                    -1
                )

            # --------------------------------
            # GPS + Database cooldown
            # --------------------------------
            current_time = time.time()

            if not detected:

                status_text = "POTHOLE NOT DETECTED"
                status_color = (0, 0, 255)
            
            else:
            
                status_text = "POTHOLE DETECTED"
                status_color = (0, 255, 0)

                # GPS every 5 sec
                if current_time - last_gps_time > gps_interval:

                    lat, lon = get_gps_location()

                    print("GPS:", lat, lon)

                    last_gps_time = current_time

                # Save every 10 sec
                if (
                    db_ready
                    and
                    current_time - last_save_time
                    > save_interval
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
            # FPS Calculation
            # --------------------------------
            fps = 1 / (current_time - prev_time)

            prev_time = current_time

            # --------------------------------
            # Display FPS
            # --------------------------------
            cv2.putText(
                frame,
                f"FPS: {int(fps)}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

            # --------------------------------
            # Display command
            # --------------------------------
            cv2.putText(
                frame,
                f"CMD: {command}",
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 0),
                2
            )

            # --------------------------------
            # Update shared frame
            # --------------------------------
            with lock:

                latest_frame = frame.copy()

            time.sleep(0.01)

        except Exception as e:

            print("Camera Error:", e)

# Start capture thread
threading.Thread(
    target=capture_loop,
    daemon=True
).start()

# --------------------------------
# MJPEG Stream Generator
# --------------------------------
def generate():

    global latest_frame

    while True:

        with lock:

            frame = (
                None
                if latest_frame is None
                else latest_frame.copy()
            )

        if frame is None:

            continue

        success, buffer = cv2.imencode(
            '.jpg',
            frame,
            [int(cv2.IMWRITE_JPEG_QUALITY), 80]
        )

        if not success:

            continue

        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' +
            buffer.tobytes() +
            b'\r\n'
        )

        time.sleep(0.03)

# --------------------------------
# Flask Routes
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

    return Response(
        generate(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@app.route('/stats')

def stats():
    """Display detection statistics"""
    
    stats_data = get_detection_stats()
    
    return {
        'total_detections': stats_data.get('total_detections', 0),
        'last_updated': str(stats_data.get('last_updated', 'N/A'))
    }

# --------------------------------
# Run Flask
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
        print("\n\nShutting down...")
        close_database()
        picam2.stop()
        print("✓ Cleanup complete")
    
    finally:
        close_database()
        picam2.stop()
