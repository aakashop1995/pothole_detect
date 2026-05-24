import socket
import json
from datetime import datetime

# shared GPS store
_latest = {"lat": None, "lon": None, "timestamp": None}

def start_gps_server():
    """Run this in a background thread on Pi"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 5001))
    server.listen(1)
    print("Waiting for GPS from Traccar...")

    while True:
        try:
            conn, _ = server.accept()
            data = conn.recv(4096).decode()
            body = data.split('\r\n\r\n', 1)[1]
            parsed = json.loads(body)
            _latest['lat'] = parsed['location']['coords']['latitude']
            _latest['lon'] = parsed['location']['coords']['longitude']
            _latest['timestamp'] = datetime.utcnow()
            print(f"GPS updated: {_latest['lat']}, {_latest['lon']}")
            conn.sendall(b"HTTP/1.1 200 OK\r\n\r\nOK")
        except Exception as e:
            print(f"GPS error: {e}")
        finally:
            conn.close()

def get_gps_location():
    return _latest['lat'], _latest['lon']
