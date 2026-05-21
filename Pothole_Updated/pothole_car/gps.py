import serial
import time

gps = None

# -----------------------------
# Connect GPS module
# -----------------------------
try:
    gps = serial.Serial("/dev/ttyS0", baudrate=9600, timeout=1)
    time.sleep(2)
    print("GPS connected")

except Exception as e:
    print("GPS not connected:", e)


# -----------------------------
# Get GPS location (lat, lon)
# -----------------------------
def get_gps_location():

    if gps is None:
        return None, None

    while True:

        try:
            line = gps.readline().decode('utf-8', errors='ignore')

            # NMEA GPGGA sentence contains location
            if line.startswith("$GPGGA"):

                parts = line.split(",")

                if len(parts) > 5 and parts[2] and parts[4]:

                    lat = convert_to_degrees(parts[2])
                    lon = convert_to_degrees(parts[4])

                    # South / West correction
                    if parts[3] == "S":
                        lat = -lat
                    if parts[5] == "W":
                        lon = -lon

                    return lat, lon

        except Exception:
            continue


# -----------------------------
# Convert NMEA → Decimal degrees
# -----------------------------
def convert_to_degrees(raw):

    if len(raw) < 6:
        return 0

    try:
        degrees = float(raw[:2])
        minutes = float(raw[2:])

        return degrees + (minutes / 60)

    except:
        return 0
