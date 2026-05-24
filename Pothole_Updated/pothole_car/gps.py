import socket
import json
from datetime import datetime

_latest = {"lat": None, "lon": None, "timestamp": None}

def start_gps_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # ← fixes port in use error
    server.bind(('0.0.0.0', 5001))
    server.listen(5)  # ← allow multiple connections in queue
    print("Waiting for GPS from Traccar...")
    while True:
        try:
            conn, _ = server.accept()  # waits for next connection
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
            conn.close()  # close this connection, loop back to accept next

def get_gps_location():
    return _latest['lat'], _latest['lon']

if __name__ == '__main__':
    start_gps_server()
