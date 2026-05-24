import socket
from pymongo import MongoClient
from datetime import datetime
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

MONGO_URI = 'mongodb://jayeshvivarekar_db_user:BioJay%4004@ac-zi1njbf-shard-00-00.udi0xw1.mongodb.net:27017,ac-zi1njbf-shard-00-01.udi0xw1.mongodb.net:27017,ac-zi1njbf-shard-00-02.udi0xw1.mongodb.net:27017/?ssl=true&replicaSet=atlas-130x6s-shard-0&authSource=admin&appName=Cluster0'

col = MongoClient(MONGO_URI)['pothole_detection']['detections']

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('0.0.0.0', 5001))
server.listen(1)
print("Waiting for GPS...")

while True:
    conn, _ = server.accept()
    data = conn.recv(4096).decode()
    try:
        # extract JSON body from HTTP request
        body = data.split('\r\n\r\n', 1)[1]
        parsed = json.loads(body)

        lat = parsed['location']['coords']['latitude']
        lon = parsed['location']['coords']['longitude']
        alt = parsed['location']['coords']['altitude']
        spd = parsed['location']['coords']['speed']
        ts  = parsed['location']['timestamp']

        doc = {
            "latitude":  lat,
            "longitude": lon,
            "altitude":  alt,
            "speed":     spd,
            "timestamp": ts,
            "device_id": parsed.get('device_id', '')
        }
        col.insert_one(doc)
        print(f"Saved → Lat: {lat}  Lon: {lon}")
        conn.sendall(b"HTTP/1.1 200 OK\r\n\r\nOK")
    except Exception as e:
        print(f"Error: {e}")
        print(f"Raw: {data}")
    conn.close()
