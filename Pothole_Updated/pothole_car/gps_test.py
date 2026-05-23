import serial
import time

gps = serial.Serial("/dev/serial0", baudrate=9600, timeout=1)

def convert_to_decimal(raw_value, direction):
    if raw_value == "":
        return None

    # Latitude has 2 degree digits, longitude has 3
    if len(raw_value) > 5:
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

    return None

print("Waiting for GPS fix...")

while True:
    try:
        line = gps.readline().decode('utf-8', errors='ignore')

        if "$GPGGA" in line:
            data = line.split(",")

            if data[2] and data[4]:

                latitude = convert_to_decimal(data[2], data[3])
                longitude = convert_to_decimal(data[4], data[5])

                print(f"Latitude : {latitude}")
                print(f"Longitude: {longitude}")
                print("--------------------------------")

        time.sleep(0.1)

    except KeyboardInterrupt:
        print("Stopped")
        break
