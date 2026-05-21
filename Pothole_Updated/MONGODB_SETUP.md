# MongoDB Atlas Setup Guide for Pothole Detection

## Overview
This guide explains how to set up MongoDB Atlas and connect your pothole detection system to save images and GPS coordinates to the cloud.

---

## 1. MongoDB Atlas Setup

### Step 1: Create a MongoDB Account
- Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
- Click "Sign Up" or "Log In" if you already have an account
- Complete the registration process

### Step 2: Create a Free Cluster
1. After logging in, click **"Create a Deployment"**
2. Choose **"Free"** tier (M0)
3. Select your preferred cloud provider (AWS, Google Cloud, or Azure)
4. Choose a region closest to you
5. Click **"Create Deployment"**
6. Wait for the cluster to be created (this takes a few minutes)

### Step 3: Set Up Network Access
1. Go to **"Network Access"** in the left sidebar
2. Click **"Add IP Address"**
3. Choose **"Allow access from anywhere"** (for development)
   - In production, use your specific IP address
4. Click **"Confirm"**

### Step 4: Create Database User
1. Go to **"Database Access"** in the left sidebar
2. Click **"Add New Database User"**
3. Enter:
   - **Username**: (e.g., `pothole_user`)
   - **Password**: (create a strong password)
4. Click **"Create User"**

### Step 5: Get Connection String
1. Go to **"Clusters"** and click your cluster
2. Click **"Connect"**
3. Choose **"Drivers"** → **"Python"**
4. Copy the connection string (it looks like):
   ```
   mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
   ```
5. Replace:
   - `username` with your database user
   - `password` with your password

---

## 2. Configure Your System

### Option A: Using Environment Variable (Recommended)

#### On Linux/Raspberry Pi:
```bash
# Add to ~/.bashrc or ~/.bash_profile
export MONGODB_URI="mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority"

# Reload the shell
source ~/.bashrc
```

#### On Windows PowerShell:
```powershell
$env:MONGODB_URI = "mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority"

# To make it permanent, use:
[System.Environment]::SetEnvironmentVariable("MONGODB_URI", "your_connection_string", "User")
```

### Option B: Direct Configuration
Edit `database.py` and replace the placeholder connection string directly:
```python
MONGODB_URI = 'mongodb+srv://your_username:your_password@cluster.mongodb.net/?retryWrites=true&w=majority'
```

---

## 3. Install Required Package

```bash
pip install pymongo
```

---

## 4. Database Schema

### Database: `pothole_detection`
### Collection: `detections`

#### Document Structure:
```json
{
  "_id": ObjectId,
  "timestamp": ISODate("2024-05-21T10:30:00Z"),
  "location": {
    "type": "Point",
    "coordinates": [longitude, latitude]
  },
  "latitude": 37.7749,
  "longitude": -122.4194,
  "image_base64": "base64_encoded_image_string",
  "image_size": [240, 320, 3],
  "confidence": null
}
```

---

## 5. Running the Application

```bash
python main.py
```

### Expected Output:
```
Camera started
✓ MongoDB connected successfully
✓ Database 'pothole_detection' and collection 'detections' ready
Command: F
Command: F
Pothole detected
GPS: 37.7749 -122.4194
✓ Pothole detection saved: ObjectId('...')
  Location: (37.77490, -122.41940)
```

---

## 6. Accessing Your Data

### Web Interface - View Stats:
Open browser and navigate to:
```
http://your_raspberry_pi_ip:5000/stats
```

Example response:
```json
{
  "total_detections": 15,
  "last_updated": "2024-05-21 10:45:30.123456"
}
```

### MongoDB Atlas UI:
1. Go to MongoDB Atlas Dashboard
2. Click your cluster → **"Collections"**
3. Navigate to `pothole_detection` → `detections`
4. View all your recorded potholes with images and GPS coordinates

### Programmatic Access:
Use MongoDB Compass (desktop app) or query via Python:

```python
from pymongo import MongoClient

client = MongoClient('mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority')
db = client['pothole_detection']
collection = db['detections']

# Get all detections
all_detections = list(collection.find({'type': {'$ne': 'metadata'}}))

# Get detection count
count = collection.count_documents({'type': {'$ne': 'metadata'}})
print(f"Total potholes detected: {count}")

# Get recent detections
recent = list(collection.find({'type': {'$ne': 'metadata'}}).sort('timestamp', -1).limit(5))

# Get detections from specific location (within 1 km)
location_detections = list(collection.find({
    'location': {
        '$near': {
            '$geometry': {
                'type': 'Point',
                'coordinates': [-122.4194, 37.7749]
            },
            '$maxDistance': 1000
        }
    }
}))
```

---

## 7. Features Available in database.py

### Functions:

#### `init_database()`
Initializes MongoDB connection and creates database/collections.
```python
from database import init_database
success = init_database()
```

#### `save_pothole_detection(frame, latitude, longitude, confidence)`
Saves a pothole detection with image and GPS coordinates.
```python
from database import save_pothole_detection
success, doc_id = save_pothole_detection(frame, lat, lon, confidence=0.95)
```

#### `get_all_detections()`
Retrieves all pothole detections.
```python
from database import get_all_detections
detections = get_all_detections()
```

#### `get_detections_by_location(latitude, longitude, radius_km)`
Finds potholes near a specific location.
```python
from database import get_detections_by_location
nearby = get_detections_by_location(37.7749, -122.4194, radius_km=2)
```

#### `get_detection_stats()`
Gets statistics about detections.
```python
from database import get_detection_stats
stats = get_detection_stats()
print(stats['total_detections'])
```

#### `close_database()`
Closes MongoDB connection gracefully.
```python
from database import close_database
close_database()
```

---

## 8. Troubleshooting

### Error: "Could not connect to MongoDB"
- ✓ Check internet connection
- ✓ Verify MongoDB URI is correct
- ✓ Ensure IP address is whitelisted in Network Access
- ✓ Check username and password are correct

### Error: "Authentication failed"
- ✓ Verify username and password match what you set in Database Access
- ✓ Ensure special characters in password are URL-encoded (e.g., `@` → `%40`)

### Images not saving
- ✓ Images are stored as base64-encoded strings (max 16MB per document)
- ✓ If images are too large, reduce resolution in detector.py

### Slow insertions
- ✓ Database operations are performed in the capture thread
- ✓ Consider running database saves in a separate thread to avoid blocking

---

## 9. Security Best Practices

⚠️ **Important for Production:**
1. Never commit `MONGODB_URI` to version control
2. Use environment variables for sensitive data
3. Create a dedicated database user with limited permissions
4. Use IP whitelisting instead of "Allow access from anywhere"
5. Enable encryption in MongoDB Atlas settings
6. Regularly backup your data

---

## 10. Next Steps

- Set up automated backups in MongoDB Atlas
- Create monitoring/alerts for detection anomalies
- Export data for analysis (e.g., heat maps of pothole locations)
- Integrate with web dashboard for visualization
- Add support for higher confidence detection thresholds before saving

---

For more information:
- [MongoDB Atlas Documentation](https://docs.atlas.mongodb.com/)
- [PyMongo Documentation](https://pymongo.readthedocs.io/)
