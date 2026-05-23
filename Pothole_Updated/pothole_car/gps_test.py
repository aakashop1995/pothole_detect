from flask import Flask
import serial
import threading
import time

app = Flask(__name__)

# ==========================================
# GPS Setup
# ==========================================

gps = serial.Serial("/dev/serial0", baudrate=9600, timeout=1)

latitude = None
longitude = None
status = "No GPS Data"

raw_gpgga = ""

satellites = ""
hdop = ""

# ==========================================
# Convert GPS Coordinates
# ==========================================

def convert_to_decimal(raw_value, direction):

    if raw_value == "":
        return None

    try:

        if direction in ['N', 'S']:

            degrees = int(raw_value[:2])
            minutes = float(raw_value[2:])

        else:

            degrees = int(raw_value[:3])
            minutes = float(raw_value[3:])

        decimal = degrees + (minutes / 60)

        if direction in ['S', 'W']:
            decimal *= -1

        return decimal

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

            line = gps.readline().decode('utf-8', errors='ignore').strip()

            if line:

                print(line)

            if "$GPGGA" in line:

                raw_gpgga = line

                data = line.split(",")

                if len(data) > 8:

                    fix = data[6]

                    satellites = data[7]

                    hdop = data[8]

                    latitude = convert_to_decimal(data[2], data[3])

                    longitude = convert_to_decimal(data[4], data[5])

                    if fix != "0":

                        status = "GPS Fix Acquired"

                    else:

                        status = "Waiting for GPS Fix"

            time.sleep(1)

        except Exception as e:

            print("GPS Error:", e)

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

    </head>

    <body style="font-family:Arial; padding:30px;">

        <h1>Live GPS Data</h1>

        <h2>Status: {status}</h2>

        <h3>Latitude : {latitude}</h3>

        <h3>Longitude: {longitude}</h3>

        <h3>Satellites: {satellites}</h3>

        <h3>HDOP: {hdop}</h3>

        <h2>Raw GPGGA Output</h2>

        <p>{raw_gpgga}</p>

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

    app.run(host="0.0.0.0", port=5000)
