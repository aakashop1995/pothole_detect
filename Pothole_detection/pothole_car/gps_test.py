import serial
import time

PORT = "/dev/ttyAMA0"

gps = serial.Serial(PORT, baudrate=9600, timeout=1)
time.sleep(2)

print("GPS started on", PORT)


def convert_to_degrees(raw, is_lon=False):

    if not raw or len(raw) < 6:
        return None

    if is_lon:
        degrees = float(raw[:3])   # longitude = 3 digits
        minutes = float(raw[3:])
    else:
        degrees = float(raw[:2])   # latitude = 2 digits
        minutes = float(raw[2:])

    return degrees + (minutes / 60)


def get_gps_location():

    while True:

        line = gps.readline().decode('utf-8', errors='ignore')
        print(line)

        if "$GPGGA" in line or "$GPRMC" in line:

            parts = line.split(",")

            try:
                lat_raw = parts[2]
                lat_dir = parts[3]
                lon_raw = parts[4]
                lon_dir = parts[5]

                if lat_raw and lon_raw:

                    lat = convert_to_degrees(lat_raw, is_lon=False)
                    lon = convert_to_degrees(lon_raw, is_lon=True)

                    if lat_dir == "S":
                        lat = -lat
                    if lon_dir == "W":
                        lon = -lon

                    return lat, lon

            except:
                continue
