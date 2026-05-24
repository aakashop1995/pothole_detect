import socket
import json
from datetime import datetime

_latest = {"lat": None, "lon": None, "timestamp": None}

def start_gps_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', 5001))
    server.listen(5)
    print("Waiting for GPS from Traccar...")
    while True:
        try:
            conn, _ = server.accept()
            data = conn.recv(4096).decode()

            # skip empty connections
            if not data:
                conn.close()
                continue

            if '\r\n\r\n' not in data:
                conn.close()
                continue

            body = data.split('\r\n\r\n', 1)[1].strip()

            if not body:
                conn.close()
                continue

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
