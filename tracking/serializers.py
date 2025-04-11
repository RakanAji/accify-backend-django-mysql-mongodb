from rest_framework import serializers
from .models import IoTDevice

class IoTDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = IoTDevice
        fields = ['id', 'device_id', 'name', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']

class LocationDataSerializer(serializers.Serializer):
    device_id = serializers.CharField(max_length=100)
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    speed = serializers.FloatField(required=False, default=0)
    angle = serializers.FloatField(required=False)  # Tambahan dari Arduino
    tilt_x = serializers.FloatField(required=False)
    tilt_y = serializers.FloatField(required=False)
    direction_x = serializers.CharField(required=False, allow_blank=True)
    direction_y = serializers.CharField(required=False, allow_blank=True)
    is_accident = serializers.BooleanField(required=False, default=False)
    additional_data = serializers.JSONField(required=False)

class AccidentSerializer(serializers.Serializer):
    _id = serializers.CharField(read_only=True)
    device_id = serializers.CharField(read_only=True)
    timestamp = serializers.DateTimeField(read_only=True)
    latitude = serializers.FloatField(read_only=True)
    longitude = serializers.FloatField(read_only=True)
    speed = serializers.FloatField(read_only=True)
    additional_data = serializers.JSONField(read_only=True)