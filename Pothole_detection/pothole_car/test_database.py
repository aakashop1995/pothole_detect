"""
Test and Example Script for MongoDB Integration
Run this to verify your MongoDB connection and explore the database
"""

from database import (
    init_database,
    get_all_detections,
    get_detection_stats,
    get_detections_by_location,
    close_database
)
import json
from bson import ObjectId


class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for MongoDB ObjectId and datetime"""
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return super().default(o)


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def test_connection():
    """Test MongoDB connection"""
    print_section("Testing MongoDB Connection")
    
    success = init_database()
    
    if success:
        print("✓ Successfully connected to MongoDB Atlas!")
        return True
    else:
        print("✗ Failed to connect to MongoDB. Check your connection string.")
        return False


def view_all_detections():
    """View all pothole detections"""
    print_section("All Pothole Detections")
    
    detections = get_all_detections()
    
    if not detections:
        print("No detections found in database.")
        return
    
    print(f"Total detections: {len(detections)}\n")
    
    for i, detection in enumerate(detections, 1):
        print(f"{i}. Detection ID: {detection.get('_id')}")
        print(f"   Timestamp: {detection.get('timestamp')}")
        print(f"   Location: ({detection.get('latitude'):.6f}, {detection.get('longitude'):.6f})")
        print(f"   Confidence: {detection.get('confidence', 'N/A')}")
        
        if detection.get('image_base64'):
            image_size = len(detection['image_base64']) / 1024  # KB
            print(f"   Image Size: {image_size:.2f} KB")
        
        print()


def view_statistics():
    """View detection statistics"""
    print_section("Detection Statistics")
    
    stats = get_detection_stats()
    
    print(f"Total Detections: {stats.get('total_detections', 0)}")
    print(f"Last Updated: {stats.get('last_updated', 'N/A')}")


def view_by_location():
    """View detections near a specific location"""
    print_section("Detections by Location")
    
    try:
        # Example: Search near San Francisco
        latitude = float(input("Enter latitude: "))
        longitude = float(input("Enter longitude: "))
        radius = float(input("Enter search radius (km): "))
        
        detections = get_detections_by_location(latitude, longitude, radius)
        
        if not detections:
            print(f"No detections found within {radius} km of ({latitude}, {longitude})")
            return
        
        print(f"\nFound {len(detections)} detections:")
        for detection in detections:
            dist_lat = abs(detection['latitude'] - latitude)
            dist_lon = abs(detection['longitude'] - longitude)
            print(f"  • ({detection['latitude']:.6f}, {detection['longitude']:.6f}) - {detection['timestamp']}")
    
    except ValueError:
        print("Invalid input. Please enter numbers.")


def export_detections_json():
    """Export detections to JSON file"""
    print_section("Export Detections")
    
    detections = get_all_detections()
    
    if not detections:
        print("No detections to export.")
        return
    
    # Remove base64 images from export (too large)
    export_data = []
    for detection in detections:
        detection_copy = detection.copy()
        if 'image_base64' in detection_copy:
            detection_copy['image_base64'] = f"<base64_image_{len(detection_copy['image_base64'])}_bytes>"
        export_data.append(detection_copy)
    
    filename = "pothole_detections_export.json"
    with open(filename, 'w') as f:
        json.dump(export_data, f, indent=2, cls=JSONEncoder)
    
    print(f"✓ Exported {len(export_data)} detections to {filename}")


def get_detection_by_id():
    """Get a specific detection by ID"""
    print_section("Get Detection by ID")
    
    try:
        detection_id = input("Enter detection ID: ")
        
        # You would need to add a function in database.py for this
        # For now, this is just a placeholder
        print("Note: ID lookup function not yet implemented in database.py")
    
    except Exception as e:
        print(f"Error: {e}")


def interactive_menu():
    """Interactive menu for testing"""
    
    print("\n" + "="*60)
    print("  MongoDB Pothole Detection - Test & Query Tool")
    print("="*60)
    
    while True:
        print("\nOptions:")
        print("  1. Test Connection")
        print("  2. View All Detections")
        print("  3. View Statistics")
        print("  4. Search by Location")
        print("  5. Export to JSON")
        print("  6. Exit")
        
        choice = input("\nSelect option (1-6): ").strip()
        
        if choice == '1':
            test_connection()
        elif choice == '2':
            view_all_detections()
        elif choice == '3':
            view_statistics()
        elif choice == '4':
            view_by_location()
        elif choice == '5':
            export_detections_json()
        elif choice == '6':
            print("\nClosing database connection...")
            close_database()
            print("✓ Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == '__main__':
    
    try:
        interactive_menu()
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        close_database()
    
    except Exception as e:
        print(f"Error: {e}")
        close_database()
