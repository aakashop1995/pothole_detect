import os
import datetime

from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, OperationFailure

from bson.binary import Binary

# ==========================================
# MONGODB CONNECTION
# ==========================================

MONGODB_URI = os.getenv(
    'MONGODB_URI',
    'mongodb://jayeshvivarekar_db_user:BioJay%4004@ac-zi1njbf-shard-00-00.udi0xw1.mongodb.net:27017,ac-zi1njbf-shard-00-01.udi0xw1.mongodb.net:27017,ac-zi1njbf-shard-00-02.udi0xw1.mongodb.net:27017/?ssl=true&replicaSet=atlas-130x6s-shard-0&authSource=admin&appName=Cluster0'
)

DATABASE_NAME = 'pothole_detection'
COLLECTION_NAME = 'detections'

# ==========================================
# GLOBALS
# ==========================================

client = None
db = None
collection = None


# ==========================================
# INITIALIZE DATABASE
# ==========================================

def init_database():

    global client, db, collection

    try:

        # Connect to MongoDB Atlas
        client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000
        )

        # Verify connection
        client.admin.command('ping')

        print("✓ MongoDB connected successfully")

        # Access database
        db = client[DATABASE_NAME]

        # Access collection
        collection = db[COLLECTION_NAME]

        # Create indexes
        collection.create_index('timestamp')
        collection.create_index('location')

        # Insert metadata if collection empty
        if collection.count_documents({}) == 0:

            collection.insert_one({
                'type': 'metadata',
                'created_at': datetime.datetime.utcnow(),
                'description': 'Pothole detection records'
            })

        print(f"✓ Database '{DATABASE_NAME}' ready")
        print(f"✓ Collection '{COLLECTION_NAME}' ready")

        return True

    except ServerSelectionTimeoutError:

        print("✗ MongoDB connection timeout")
        return False

    except OperationFailure as e:

        print(f"✗ MongoDB operation error: {e}")
        return False

    except Exception as e:

        print(f"✗ Database init error: {e}")
        return False


# ==========================================
# SAVE POTHOLE DETECTION
# ==========================================

def save_pothole_detection(frame, latitude, longitude, confidence=None):

    global collection

    if collection is None:

        print("✗ Database not initialized")
        return False, None

    if latitude is None or longitude is None:

        print("⚠ GPS coordinates missing")
        return False, None

    try:

        # ==================================
        # ENCODE IMAGE AS BINARY JPEG
        # ==================================

        image_binary = None

        if frame is not None:

            success, buffer = __encode_frame(frame)

            if success:
                image_binary = Binary(buffer)

        # ==================================
        # CREATE DOCUMENT
        # ==================================

        document = {

            'timestamp': datetime.datetime.utcnow(),

            'location': {
                'type': 'Point',
                'coordinates': [longitude, latitude]
            },

            'latitude': latitude,
            'longitude': longitude,

            # Binary image storage
            'image_binary': image_binary,

            'image_size': frame.shape if frame is not None else None,

            'confidence': confidence
        }

        # ==================================
        # INSERT DOCUMENT
        # ==================================

        result = collection.insert_one(document)

        print(f"✓ Detection saved: {result.inserted_id}")

        print(f"  Latitude : {latitude:.6f}")
        print(f"  Longitude: {longitude:.6f}")

        return True, result.inserted_id

    except Exception as e:

        print(f"✗ Save error: {e}")

        return False, None


# ==========================================
# ENCODE FRAME
# ==========================================

def __encode_frame(frame):

    import cv2

    success, buffer = cv2.imencode(
        '.jpg',
        frame,
        [int(cv2.IMWRITE_JPEG_QUALITY), 80]
    )

    if success:

        return True, buffer.tobytes()

    return False, None


# ==========================================
# GET ALL DETECTIONS
# ==========================================

def get_all_detections():

    global collection

    if collection is None:

        print("✗ Database not initialized")
        return []

    try:

        detections = list(
            collection.find({
                'type': {'$ne': 'metadata'}
            })
        )

        print(f"✓ Retrieved {len(detections)} detections")

        return detections

    except Exception as e:

        print(f"✗ Retrieval error: {e}")

        return []


# ==========================================
# GET DETECTIONS BY LOCATION
# ==========================================

def get_detections_by_location(latitude, longitude, radius_km=1):

    global collection

    if collection is None:

        print("✗ Database not initialized")
        return []

    try:

        detections = list(collection.find({

            'location': {

                '$near': {

                    '$geometry': {
                        'type': 'Point',
                        'coordinates': [longitude, latitude]
                    },

                    '$maxDistance': radius_km * 1000
                }
            }
        }))

        print(f"✓ Found {len(detections)} nearby detections")

        return detections

    except Exception as e:

        print(f"✗ Location query error: {e}")

        return []


# ==========================================
# DATABASE STATS
# ==========================================

def get_detection_stats():

    global collection

    if collection is None:

        return {}

    try:

        total = collection.count_documents({
            'type': {'$ne': 'metadata'}
        })

        stats = {

            'total_detections': total,

            'last_updated': datetime.datetime.utcnow()
        }

        return stats

    except Exception as e:

        print(f"✗ Stats error: {e}")

        return {}


# ==========================================
# CLOSE DATABASE
# ==========================================

def close_database():

    global client

    if client is not None:

        try:

            client.close()

            print("✓ MongoDB connection closed")

        except Exception as e:

            print(f"✗ Close DB error: {e}")


# ==========================================
# TEST
# ==========================================

if __name__ == "__main__":

    init_database()
