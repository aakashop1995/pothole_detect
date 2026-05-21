import os
import base64
import datetime
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, OperationFailure

# MongoDB Atlas connection string
# Set via environment variable or replace with your actual connection string
MONGODB_URI = os.getenv(
    'MONGODB_URI',
    'mongodb://jayeshvivarekar_db_user:BioJay%4004@ac-zi1njbf-shard-00-00.udi0xw1.mongodb.net:27017,ac-zi1njbf-shard-00-01.udi0xw1.mongodb.net:27017,ac-zi1njbf-shard-00-02.udi0xw1.mongodb.net:27017/?ssl=true&replicaSet=atlas-130x6s-shard-0&authSource=admin&appName=Cluster0'

)

DATABASE_NAME = 'pothole_detection'
COLLECTION_NAME = 'detections'

# MongoDB connection
client = None
db = None
collection = None


def init_database():
    """
    Initialize MongoDB connection and create database/collections if they don't exist
    """
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
        
        # Access or create database
        db = client[DATABASE_NAME]
        
        # Access or create collection
        collection = db[COLLECTION_NAME]
        
        # Create indexes for better query performance
        collection.create_index('timestamp')
        collection.create_index('location')
        
        # Create collection metadata if empty
        if collection.count_documents({}) == 0:
            collection.insert_one({
                'type': 'metadata',
                'created_at': datetime.datetime.utcnow(),
                'description': 'Pothole detection records'
            })
        
        print(f"✓ Database '{DATABASE_NAME}' and collection '{COLLECTION_NAME}' ready")
        return True
        
    except ServerSelectionTimeoutError:
        print("✗ Error: Could not connect to MongoDB. Check your connection string and internet.")
        return False
    except OperationFailure as e:
        print(f"✗ MongoDB Operation Error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error initializing database: {e}")
        return False


def save_pothole_detection(frame, latitude, longitude, confidence=None):
    """
    Save pothole detection to MongoDB
    
    Parameters:
    - frame: OpenCV frame (numpy array)
    - latitude: GPS latitude coordinate
    - longitude: GPS longitude coordinate
    - confidence: Detection confidence score (optional)
    
    Returns:
    - bool: True if saved successfully, False otherwise
    - ObjectId: MongoDB document ID if successful, None otherwise
    """
    
    global collection
    
    if collection is None:
        print("✗ Database not initialized. Call init_database() first.")
        return False, None
    
    if latitude is None or longitude is None:
        print("⚠ Warning: GPS coordinates are missing")
        return False, None
    
    try:
        # Convert frame to base64 for storage
        if frame is not None:
            _, buffer = __encode_frame(frame)
            image_base64 = base64.b64encode(buffer).decode('utf-8')
        else:
            image_base64 = None
        
        # Create document
        document = {
            'timestamp': datetime.datetime.utcnow(),
            'location': {
                'type': 'Point',
                'coordinates': [longitude, latitude]  # GeoJSON format: [lon, lat]
            },
            'latitude': latitude,
            'longitude': longitude,
            'image_base64': image_base64,
            'image_size': frame.shape if frame is not None else None,
            'confidence': confidence
        }
        
        # Insert into collection
        result = collection.insert_one(document)
        
        print(f"✓ Pothole detection saved: {result.inserted_id}")
        print(f"  Location: ({latitude:.6f}, {longitude:.6f})")
        
        return True, result.inserted_id
        
    except Exception as e:
        print(f"✗ Error saving to database: {e}")
        return False, None


def __encode_frame(frame):
    """Helper function to encode frame as JPEG"""
    import cv2
    
    success, buffer = cv2.imencode(
        '.jpg',
        frame,
        [int(cv2.IMWRITE_JPEG_QUALITY), 80]
    )
    
    return success, buffer.tobytes() if success else (False, b'')


def get_all_detections():
    """
    Retrieve all pothole detections from database
    
    Returns:
    - list: List of detection documents
    """
    
    global collection
    
    if collection is None:
        print("✗ Database not initialized.")
        return []
    
    try:
        detections = list(collection.find({'type': {'$ne': 'metadata'}}))
        print(f"✓ Retrieved {len(detections)} detections")
        return detections
        
    except Exception as e:
        print(f"✗ Error retrieving detections: {e}")
        return []


def get_detections_by_location(latitude, longitude, radius_km=1):
    """
    Retrieve pothole detections near a specific location
    
    Parameters:
    - latitude, longitude: Center point
    - radius_km: Search radius in kilometers
    
    Returns:
    - list: Detections within radius
    """
    
    global collection
    
    if collection is None:
        print("✗ Database not initialized.")
        return []
    
    try:
        # GeoJSON query
        detections = list(collection.find({
            'location': {
                '$near': {
                    '$geometry': {
                        'type': 'Point',
                        'coordinates': [longitude, latitude]
                    },
                    '$maxDistance': radius_km * 1000  # Convert to meters
                }
            }
        }))
        
        print(f"✓ Found {len(detections)} detections near location")
        return detections
        
    except Exception as e:
        print(f"✗ Error querying by location: {e}")
        return []


def get_detection_stats():
    """
    Get statistics about pothole detections
    
    Returns:
    - dict: Statistics
    """
    
    global collection
    
    if collection is None:
        return {}
    
    try:
        total = collection.count_documents({'type': {'$ne': 'metadata'}})
        
        stats = {
            'total_detections': total,
            'last_updated': datetime.datetime.utcnow()
        }
        
        return stats
        
    except Exception as e:
        print(f"✗ Error getting statistics: {e}")
        return {}


def close_database():
    """Close MongoDB connection"""
    global client
    
    if client is not None:
        try:
            client.close()
            print("✓ MongoDB connection closed")
        except Exception as e:
            print(f"✗ Error closing database: {e}")

if __name__ == "__main__":

    init_database()