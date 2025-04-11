from django.db import models
from accounts.models import User
from pymongo import MongoClient
from django.conf import settings
import datetime

# Model relasional untuk MySQL (metadata)
class IoTDevice(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="devices")
    device_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.device_id})"

# MongoDB connection handler (untuk operasi ke MongoDB)
class MongoDBManager:
    def __init__(self):
        # Connect to MongoDB using settings from Django
        self.client = MongoClient(
            'mongodb://mongoAccify_user:123@localhost:27017/mongoAccify_db?authSource=mongoAccify_db'
        )
        self.db = self.client['mongoAccify_db']
    
    def save_location_data(self, device_id, data):
        """Save device location and speed data to MongoDB"""
        collection = self.db['location_data']
        document = {
            'device_id': device_id,
            'timestamp': datetime.datetime.now(),
            'latitude': data.get('latitude'),
            'longitude': data.get('longitude'),
            'speed': data.get('speed', 0),
            'angle': data.get('angle'),
            'tilt_x': data.get('tilt_x'),
            'tilt_y': data.get('tilt_y'),
            'direction_x': data.get('direction_x'),
            'direction_y': data.get('direction_y'),
            'is_accident': data.get('is_accident', False),
            'additional_data': data.get('additional_data', {})
        }
        result = collection.insert_one(document)
        return result.inserted_id
    
    def get_recent_location(self, device_id, limit=1):
        """Get the most recent location data for a device"""
        collection = self.db['location_data']
        cursor = collection.find({'device_id': device_id}).sort('timestamp', -1).limit(limit)
        return list(cursor)
    
    def get_accident_data(self, device_id=None):
        """Get all accident data, optionally filtered by device_id"""
        collection = self.db['location_data']
        query = {'is_accident': True}
        if device_id:
            query['device_id'] = device_id
        cursor = collection.find(query).sort('timestamp', -1)
        return list(cursor)