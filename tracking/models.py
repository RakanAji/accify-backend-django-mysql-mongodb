from django.db import models
from accounts.models import User
from pymongo import MongoClient
from django.conf import settings
import datetime
from django.utils import timezone

# Model relasional untuk MySQL (metadata)
class IoTDevice(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="devices")
    device_id = models.CharField(max_length=100, unique=True)
    ephemeral_id = models.CharField(max_length=32, unique=True, null=True, blank=True)
    device_token = models.CharField(max_length=64, unique=True, null=True, blank=True)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.device_id})"

# MongoDB connection handler (untuk operasi ke MongoDB)
class MongoDBManager:
    def __init__(self):
        # Connect to MongoDB using settings from Django
        uri = (
            f"mongodb://"
            f"{settings.MONGO_USER}:{settings.MONGO_PASSWORD}@"
            f"{settings.MONGO_HOST}:{settings.MONGO_PORT}/"
            f"{settings.MONGO_DB}"
            f"?authSource=admin"
        )
        self.client = MongoClient(uri)
        self.db = self.client[settings.MONGO_DB]

    def _convert_timestamps_to_wib(self, results):
        """Helper method untuk konversi timestamp ke WIB."""
        local_tz = timezone.get_default_timezone()
        for doc in results:
            if 'timestamp' in doc and doc['timestamp']:
                original_timestamp = doc['timestamp']
                
                # Jika timestamp naive, anggap UTC dan buat aware
                if timezone.is_naive(original_timestamp):
                    aware_timestamp = timezone.make_aware(original_timestamp, datetime.timezone.utc)
                else: # Jika sudah aware
                    aware_timestamp = original_timestamp

                # Konversi ke zona waktu lokal (WIB) dan update dokumen
                doc['timestamp'] = aware_timestamp.astimezone(local_tz)
        return results
    
    def save_location_data(self, device_id, data):
        """Save device location and speed data to MongoDB"""
        collection = self.db['location_data']
        document = {
            'device_id': device_id,
            'timestamp': timezone.now(),
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
        results = list(cursor)
        # Panggil helper konversi sebelum return
        return self._convert_timestamps_to_wib(results)
    
    def get_accident_data(self, device_id=None):
        """Get all accident data, optionally filtered by device_id"""
        collection = self.db['location_data']
        query = {'is_accident': True}
        if device_id:
            query['device_id'] = device_id
        cursor = collection.find(query).sort('timestamp', -1)
        results = list(cursor)
        # Panggil helper konversi sebelum return
        return self._convert_timestamps_to_wib(results)