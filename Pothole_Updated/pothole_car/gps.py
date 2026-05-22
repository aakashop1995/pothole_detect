import serial
import time

gps = None

try:
    gps = serial.Serial("/dev/ttyS0", baudrate=9600, timeout=1)
    time.sleep(2)
    print("GPS connected")
except Exception as e:
    print("GPS not connected:", e)


def get_gps_location():
    if gps is None:
        return None, None

    max_attempts = 10  # give up after 10 lines

    for _ in range(max_attempts):
        try:
            line = gps.readline().decode('utf-8', errors='ignore').strip()

            if line.startswith("$GPGGA"):
                parts = line.split(",")
                if len(parts) > 5 and parts[2] and parts[4]:
                    lat = convert_to_degrees(parts[2])
                    lon = convert_to_degrees(parts[4])
                    if parts[3] == "S":
                        lat = -lat
                    if parts[5] == "W":
                        lon = -lon
                    return lat, lon

        except Exception:
            continue

    return None, None


def convert_to_degrees(raw):
    if len(raw) < 6:
        return 0
    try:
        degrees = float(raw[:2])
        minutes = float(raw[2:])
        return degrees + (minutes / 60)
    except:
        return 0
