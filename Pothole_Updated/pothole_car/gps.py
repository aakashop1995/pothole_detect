import socket
import pynmea2
import time

# ======================================
# UDP SETTINGS
# ======================================

UDP_IP = "0.0.0.0"
UDP_PORT = 5001

# ======================================
# GLOBAL GPS VALUES
# ======================================

latest_latitude = None
latest_longitude = None

# ======================================
# CREATE SOCKET
# ======================================

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

sock.bind((UDP_IP, UDP_PORT))

print(f"GPS server listening on port {UDP_PORT}")

# ======================================
# START GPS SERVER
# ======================================

def start_gps_server():

    global latest_latitude
    global latest_longitude

    last_print_time = 0

    while True:

        try:

            # Receive UDP packet
            data, addr = sock.recvfrom(1024)

            # Decode GPS line
            line = data.decode(errors='ignore').strip()

            # Parse only GGA
            if line.startswith("$GPGGA") or line.startswith("$GNGGA"):

                try:

                    # Parse NMEA sentence
                    msg = pynmea2.parse(line)

                    latitude = msg.latitude
                    longitude = msg.longitude

                    # Save latest values
                    latest_latitude = latitude
                    latest_longitude = longitude

                    # Print every 2 sec only
                    current_time = time.time()

                    if current_time - last_print_time > 2:

                        print(f"Latitude : {latitude}")
                        print(f"Longitude: {longitude}")
                        print("-------------------")

                        last_print_time = current_time

                except Exception as e:

                    print("GPS parse error:", e)

        except Exception as e:

            print("GPS receive error:", e)


# ======================================
# GET GPS LOCATION
# ======================================

def get_gps_location():

    return latest_latitude, latest_longitude
