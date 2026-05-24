import socket
import pynmea2

# ======================================
# UDP SETTINGS
# ======================================

UDP_IP = "0.0.0.0"
UDP_PORT = 5001

# ======================================
# CREATE SOCKET
# ======================================

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

sock.bind((UDP_IP, UDP_PORT))

print("Waiting for GPS data...")

# ======================================
# RECEIVE GPS DATA
# ======================================

while True:

    # Receive UDP packet
    data, addr = sock.recvfrom(1024)

    # Decode packet
    line = data.decode(errors='ignore').strip()

    # Print raw GPS line (optional)
    print(line)

    # Parse only GGA sentences
    if line.startswith("$GPGGA") or line.startswith("$GNGGA"):

        try:

            # Parse NMEA sentence
            msg = pynmea2.parse(line)

            latitude = msg.latitude
            longitude = msg.longitude

            print("Latitude :", latitude)
            print("Longitude:", longitude)
            print("-------------------")

        except Exception as e:

            print("Parse error:", e)
