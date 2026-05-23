from flask import Flask
import serial
import threading
import time

app = Flask(__name__)

# ==========================================
# GPS Setup
# ==========================================

gps = serial.Serial(
    "/dev/serial0",
    baudrate=9600,
    timeout=1
)

latitude = None
longitude = None
status = "Waiting for GPS Data"

raw_gpgga = ""

satellites = "0"
hdop = "99.99"

# ==========================================
# Convert GPS Coordinates
# ==========================================

def convert_to_decimal(raw_value, direction):

    if raw_value == "":
        return None

    try:

        # Latitude
        if direction in ['N', 'S']:

            degrees = int(raw_value[:2])
            minutes = float(raw_value[2:])

        # Longitude
        else:

            degrees = int(raw_value[:3])
            minutes = float(raw_value[3:])

        decimal = degrees + (minutes / 60)

        if direction in ['S', 'W']:
            decimal *= -1

        return round(decimal, 6)

    except:
        return None

# ==========================================
# GPS Reader Thread
# ==========================================

def read_gps():

    global latitude
    global longitude
    global status
    global raw_gpgga
    global satellites
    global hdop

    print("GPS Reader Started")

    while True:

        try:

            line = gps.readline().decode(
                'utf-8',
                errors='ignore'
            ).strip()

            if line:

                print(line)

            # Read only GPGGA sentence
            if line.startswith("$GPGGA"):

                raw_gpgga = line

                data = line.split(",")

                if len(data) > 8:

                    fix = data[6]

                    satellites = data[7]
                    hdop = data[8]

                    latitude = convert_to_decimal(
                        data[2],
                        data[3]
                    )

                    longitude = convert_to_decimal(
                        data[4],
                        data[5]
                    )

                    # GPS Fix Status
                    if fix != "0":

                        status = "GPS Fix Acquired"

                    else:

                        status = "Waiting for GPS Fix"

            time.sleep(0.01)

        except Exception as e:

            print("GPS Error:", e)

            time.sleep(1)

# ==========================================
# Flask Route
# ==========================================

@app.route("/")

def home():

    return f"""

    <html>

    <head>

        <title>GPS Tracker</title>

        <meta http-equiv="refresh" content="2">

        <style>

            body {{
                font-family: Arial;
                padding: 30px;
                background: #f5f5f5;
            }}

            .card {{
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0px 0px 10px rgba(0,0,0,0.1);
                max-width: 700px;
            }}

            h1 {{
                color: #333;
            }}

            p {{
                font-size: 18px;
            }}

        </style>

    </head>

    <body>

        <div class="card">

            <h1>Live GPS Data</h1>

            <h2>Status: {status}</h2>

            <p><b>Latitude:</b> {latitude}</p>

            <p><b>Longitude:</b> {longitude}</p>

            <p><b>Satellites:</b> {satellites}</p>

            <p><b>HDOP:</b> {hdop}</p>

            <h3>Raw GPGGA Output</h3>

            <p>{raw_gpgga}</p>

        </div>

    </body>

    </html>

    """

# ==========================================
# Main
# ==========================================

if __name__ == "__main__":

    gps_thread = threading.Thread(target=read_gps)

    gps_thread.daemon = True

    gps_thread.start()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
